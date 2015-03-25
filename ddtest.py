import json
import signal
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import RequestHandler, Application, url
from jobs.manager import JobManager, DownloadAndPackJobItem

is_closing = False


def signal_handler(signum, frame):
    global is_closing
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        IOLoop.instance().stop()


class HelloHandler(RequestHandler):
    def get(self):
        print(self.request)
        print(self.path_args)

        resp = {'hello': 'world'}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class JobListHandler(RequestHandler):
    def get(self):

        resp = {'jobs': [x.json() for x in JobManager.instance().joblist]}

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class JobAddHandler(RequestHandler):
    def post(self):

        payload = json.loads(self.get_argument('body'))
        print(payload)

        job = DownloadAndPackJobItem()
        job.from_json(payload)
        JobManager.instance().add_job(job)

        resp = {'result': 'ok'}
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


class JobDelHandler(RequestHandler):
    def post(self):

        payload = json.loads(self.get_argument('body'))
        print(payload)

        jobid = int(payload['jobid'])
        resp = {'result': 'ok'}

        JobManager.instance().remove_job(jobid)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))


def make_app():
    return Application([
        url(r"/", HelloHandler),
        url(r"/jobs/list", JobListHandler),
        url(r"/jobs/add", JobAddHandler),
        url(r"/jobs/del", JobDelHandler)])


def main():
    app = make_app()
    app.listen(8888)
    signal.signal(signal.SIGINT, signal_handler)
    PeriodicCallback(try_exit, 100).start()
    IOLoop.current().start()

if __name__ == '__main__':
    main()
