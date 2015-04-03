# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import string
import re

# http requests
import requests

# logging
import logging
import logging.handlers

def remove_invalid_path_chars(s):
    valid_chars = "-_.() {}{}".format(string.ascii_letters, string.digits)
    return re.sub(' +', ' ', ''.join(c for c in s if c in valid_chars)).strip()


def list_diff(a, b):
        b = set(b)
        return [aa for aa in a if aa not in b]


'''
This library is provided to allow standard python logging
to output log data as JSON formatted strings
'''
import logging
import json
import re
import datetime
import traceback

from inspect import istraceback

#Support order in python 2.7 and 3
try:
    from collections import OrderedDict
except ImportError:
    pass

# skip natural LogRecord attributes
# http://docs.python.org/library/logging.html#logrecord-attributes
RESERVED_ATTRS = (
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module',
    'msecs', 'message', 'msg', 'name', 'pathname', 'process',
    'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName')

RESERVED_ATTR_HASH = dict(zip(RESERVED_ATTRS, RESERVED_ATTRS))


def merge_record_extra(record, target, reserved=RESERVED_ATTR_HASH):
    """
    Merges extra attributes from LogRecord object into target dictionary
    :param record: logging.LogRecord
    :param target: dict to update
    :param reserved: dict or list with reserved keys to skip
    """
    for key, value in record.__dict__.items():
        #this allows to have numeric keys
        if (key not in reserved
            and not (hasattr(key, "startswith")
                     and key.startswith('_'))):
            target[key] = value
    return target

class MyHTTPHandler(logging.Handler):
    """
    A class which sends records to a Web server, using either GET or
    POST semantics.
    """
    def __init__(self, url):
        """
        Initialize the instance with the request URL
        """
        logging.Handler.__init__(self)

        self.url = url

    def mapLogRecord(self, record):

        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text ...
            dummy = self.format(record)
        # See issue #14436: If msg or args are objects, they may not be
        # available on the receiving end. So we convert the msg % args
        # to a string, save it as msg and zap the args.
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = None
        d['exc_info'] = None
        return json.dumps(d)

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Web server as a percent-encoded dictionary
        """
        try:
            data = self.mapLogRecord(record)
            # asd = self.mapLogRecord(record)
            #formatted = self.formatter.format(record)

            #data = {"body": formatted}

            r = requests.post(self.url, data)
        except Exception as e:
            print(e, record)

def setup_http_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    http_handler = MyHTTPHandler('http://localhost:8888/log/write')
    logger.addHandler(http_handler)
    return logger
