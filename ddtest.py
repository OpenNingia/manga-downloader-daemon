import json
import signal
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import RequestHandler, Application, url

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

        resp = { 'hello': 'world' }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))

class JobsHandler(RequestHandler):
    def get(self):
        resp = { 'job': 'list' }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))

def make_app():
    return Application([
        url(r"/", HelloHandler),
        url(r"/jobs", JobsHandler),
        ])

def main():
    app = make_app()
    app.listen(8888)
    signal.signal(signal.SIGINT, signal_handler)
    PeriodicCallback(try_exit, 100).start()
    IOLoop.current().start()

if __name__ == '__main__':
    main()