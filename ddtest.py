import os
import json
import signal
from tornado.ioloop import IOLoop, PeriodicCallback

import tornado.web
import tornado.httpserver

from jobs.manager import JobManager, JobItem, DownloadAndPackJobItem

is_closing = False


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


def job_status_to_string(stat):
    if stat == JobItem.JOB_STATUS_STOPPED:
        return "Stopped"
    if stat == JobItem.JOB_STATUS_PAUSED:
        return "Paused"
    if stat == JobItem.JOB_STATUS_QUEUED:
        return "Queued"
    if stat == JobItem.JOB_STATUS_RUNNING:
        return "Downloading"
    if stat == JobItem.JOB_STATUS_COMPLETED:
        return "Completed"
    if stat == JobItem.JOB_STATUS_ERROR:
        return "Error"
    return "Unknown"


class IndexHandler(tornado.web.RequestHandler):
    def get(self):

        proto = self.request.protocol
        host = self.request.host
        # port = self.request.port

        pbhost = '{}://{}'.format(proto, host)

        self.render('index.html', postback_host=pbhost)


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

            if 'status' in d:
                d['status'] = job_status_to_string(d['status'])

            data.append({
                "id": i+1,
                "values": d
            })

        resp = {
            "metadata": [
                {"name": "jobid", "label": "JOBID",
                 "datatype": "integer", "editable": False},

                {"name": "status", "label": "STATUS",
                 "datatype": "string", "editable": False},

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

        payload = json.loads(self.get_argument('body'))
        print(payload)

        job = DownloadAndPackJobItem()
        job.from_json(payload)
        JobManager.instance().add_job(job)

        resp = {'result': 'ok'}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class JobDelHandler(tornado.web.RequestHandler):
    def post(self):

        payload = json.loads(self.get_argument('body'))
        print(payload)

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
            tornado.web.url(r"/jobs/del", JobDelHandler)]

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
