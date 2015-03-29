# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import string
import re


def remove_invalid_path_chars(s):
    valid_chars = "-_.() {}{}".format(string.ascii_letters, string.digits)
    return re.sub(' +', ' ', ''.join(c for c in s if c in valid_chars)).strip()


def list_diff(a, b):
        b = set(b)
        return [aa for aa in a if aa not in b]