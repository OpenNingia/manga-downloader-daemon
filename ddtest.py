import os
import sys
import json
import signal

from tornado.ioloop import IOLoop, PeriodicCallback

import tornado.web
import tornado.httpserver

from jobs.manager import JobManager, JobItem, DownloadAndPackJobItem

is_closing = False

# logging
import logging
import logging.handlers

__version__ = "0.1"

APP_BRIEF = "mangadd"
APP_NAME  = "manga-downloader-daemon"
APP_DESC  = "Manga Downloader Daemon"
APP_VER   = __version__
APP_ORG   = "openningia.org"

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")

def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""

    if we_are_frozen():
        return os.path.dirname(sys.executable)

    return os.path.dirname(__file__)

SCRIPT_PATH     = module_path()
LOG_DIR         = os.path.join(SCRIPT_PATH, 'logs')

def log_setup(base_path, base_name):
    # check base path
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    # set up logging to file

    root = logging.getLogger('')

    # set the level of the root logger
    root.setLevel(logging.DEBUG)

    # define the file formatter
    file_fmt = logging.Formatter('%(asctime)s %(name)-12s ' +
                                 '%(levelname)-8s %(message)s')

    # define log rotation
    rotation = logging.handlers.TimedRotatingFileHandler(
                filename=os.path.join(base_path, base_name),
                when='midnight',
                backupCount = 15)

    rotation.setFormatter(file_fmt)

    # add the handlers to the root logger
    logging.getLogger('').addHandler(rotation)


def signal_handler(signum, frame):
    global is_closing
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        IOLoop.instance().stop()
        # stop background processes
        JobManager.instance().stop()


def job_run():
    JobManager.instance().run_once()
    try_exit()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):

        proto = self.request.protocol
        host = self.request.host
        # port = self.request.port

        pbhost = '{}://{}'.format(proto, host)

        self.render('index.html', postback_host=pbhost)


class LogHandler(tornado.web.RequestHandler):
    def post(self):
        # print(self.request.body)

        log = logging.getLogger("app")

        #payload = json.loads(self.get_argument('body'))
        payload = json.loads(self.request.body.decode('utf-8'))
        #print('payload', payload)

        record = logging.makeLogRecord(payload)
        # print('record', record)
        log.handle(record)

        self.set_status(204)
        #self.finish()


class JobListHandler(tornado.web.RequestHandler):
    def get(self):

        resp = [x.json() for x in JobManager.instance().joblist]

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class JobListWithMetadataHandler(tornado.web.RequestHandler):
    def get(self):

        # [{"jobid": 1, "status": 0, "label": "", "to": 1, "url": "asdasd",
        # "profile": "kobo_aura_hd", "format": "cbz", "progress": 0, "from": 1, "volume": -1}]
        #
        #
        data = []
        for i, d in enumerate([x.json() for x in
                               JobManager.instance().joblist]):

            #if 'status' in d:
            #    d['status'] = job_status_to_string(d['status'])

            data.append({
                "id": i+1,
                "values": d
            })

        resp = {
            "metadata": [
                {"name": "jobid", "label": "JOBID",
                 "datatype": "integer", "editable": False},

                #{"name": "status", "label": "STATUS",
                # "datatype": "string", "editable": False},


                {"name": "status", "label": "STATUS",
                 "datatype": "integer", "editable": False, "values":
                    {
                        JobItem.JOB_STATUS_STOPPED: "Stopped",
                        JobItem.JOB_STATUS_PAUSED: "Paused",
                        JobItem.JOB_STATUS_QUEUED: "Queued",
                        JobItem.JOB_STATUS_RUNNING: "Downloading",
                        JobItem.JOB_STATUS_COMPLETED: "Completed",
                        JobItem.JOB_STATUS_ERROR: "Error"
                    }},


                {"name": "from", "label": "FROM CHAPTER",
                 "datatype": "integer", "editable": False},

                {"name": "to", "label": "TO CHAPTER",
                 "datatype": "integer", "editable": False},

                {"name": "volume", "label": "VOLUME",
                 "datatype": "integer", "editable": False},

                {"name": "profile", "label": "PROFILE",
                 "datatype": "string", "editable": True, "values":
                    {
                        "kobo_aura_hd": "Kobo Aura HD",
                        "kindle4nt": "Kindle 4 NT"
                    }},

                {"name": "format", "label": "FORMAT",
                 "datatype": "string", "editable": True, "values":
                    {
                        "cbz": "CBZ",
                        "epub": "EPUB",
                        "mobi": "MOBI"
                    }},

                {"name": "progress", "label": "PROGRESS",
                 "datatype": "integer", "editable": False},

                {"name": "pages_downloaded", "label": "DOWNLOADED PAGES",
                 "datatype": "integer", "editable": False},

                {"name": "pages_count", "label": "TOTAL PAGES",
                 "datatype": "integer", "editable": False},

                {"name": "url", "label": "URL",
                 "datatype": "string", "editable": False}
            ],

            "data": data
        }

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class JobAddHandler(tornado.web.RequestHandler):
    def post(self):

        log = logging.getLogger('web')

        payload = json.loads(self.get_argument('body'))
        log.debug('addjob request: {}'.format(payload))

        job = DownloadAndPackJobItem()
        job.from_json(payload)
        JobManager.instance().add_job(job)

        resp = {'result': 'ok'}
        self.set_header("Content-Type", "application/x-www-form-urlencoded")
        self.write(json.dumps(resp))


class JobDelHandler(tornado.web.RequestHandler):
    def post(self):

        log = logging.getLogger('web')

        payload = json.loads(self.get_argument('body'))
        log.debug('deljob request: {}'.format(payload))

        jobid = int(payload['jobid'])
        resp = {'result': 'ok'}

        JobManager.instance().remove_job(jobid)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            tornado.web.url(r"/", IndexHandler),
            tornado.web.url(r"/jobs/list", JobListHandler),
            tornado.web.url(r"/jobs/listex", JobListWithMetadataHandler),
            tornado.web.url(r"/jobs/add", JobAddHandler),
            tornado.web.url(r"/jobs/del", JobDelHandler),
            tornado.web.url(r"/log/write", LogHandler)]

        settings = {
            "template_path": os.path.join(os.path.dirname(__file__), "webui"),
            "static_path": os.path.join(os.path.dirname(__file__), "webui"),
            # "cookie_secret": "gesrgergesrgesg34534tsfgdfgd",
            "xsrf_cookies": False,
            "debug": True
        }

        tornado.web.Application.__init__(self, handlers, **settings)


def make_app():
    return Application()


def main():

    try:
        os.makedirs(LOG_DIR)
    except:
        print('cannot create log directory')
    finally:
        log_setup(LOG_DIR, "{}.web.log".format(APP_BRIEF))

    # resume jobs
    JobManager.instance().load_jobs()

    app = make_app()
    app.listen(8888)
    signal.signal(signal.SIGINT, signal_handler)
    PeriodicCallback(job_run, 100).start()
    # PeriodicCallback(try_exit, 100).start()
    IOLoop.current().start()

if __name__ == '__main__':
    main()
