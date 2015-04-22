import os.path as path
import threading

import flask
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer
from tornado.web import FallbackHandler, Application
import tornado.httpserver

import meteorpi_fdb


DEFAULT_DB_PATH = 'localhost:/var/lib/firebird/2.5/data/meteorpi.fdb'
DEFAULT_FILE_PATH = path.expanduser("~/meteorpi_files")
DEFAULT_PORT = 12345


class MeteorServer():
    """HTTP server which responds to API requests and returns JSON formatted domain objects"""

    class IOLoopThread(threading.Thread):
        """A thread used to run the Tornado IOLoop in a non-blocking fashion, mostly for testing"""

        def __init__(self):
            threading.Thread.__init__(self, name='IOLoopThread')
            self.loop = IOLoop.instance()

        def run(self):
            self.loop.start()

        def stop(self):
            self.loop.stop()

    def __init__(self, db_path=DEFAULT_DB_PATH, file_store_path=DEFAULT_FILE_PATH, port=DEFAULT_PORT):
        app = flask.Flask(__name__)
        self.db = meteorpi_fdb.MeteorDatabase(db_path=db_path, file_store_path=file_store_path)
        tornado_application = Application([(r'.*', FallbackHandler, dict(fallback=WSGIContainer(app)))])
        self.server = tornado.httpserver.HTTPServer(tornado_application)
        self.port = port

        # Routes below this point

        @app.route('/cameras', methods=['GET'])
        def hello_world():
            cameras = self.db.get_cameras()
            return flask.jsonify({'cameras':cameras})

        @app.route('/cameras/<camera_id>', methods=['GET'])
        def hello_world_again(camera_id):
            return 'Hello World Again {0}'.format(camera_id)

    def __str__(self):
        return 'MeteorServer(port={0}, db_path={1}, file_path={2})'.format(self.port, self.db.db_path,
                                                                           self.db.file_store_path)

    def base_url(self):
        return 'http://localhost:{0}/'.format(self.port)

    def start_non_blocking(self):
        """Start an IOLoop in a new thread, returning a function which will stop the new thread and join it"""
        loop = self.IOLoopThread()
        self.server.listen(self.port)
        loop.start()

        def stop_function():
            self.server.stop()
            loop.stop()
            loop.join()

        return stop_function

    def start(self):
        """Start an IOLoop and server in the current thread, this will block until killed"""
        self.server.listen(self.port)
        IOLoop.instance().start()


"""Start a blocking server if run as a script"""
if __name__ == "__main__":
    server = MeteorServer()
    server.start()
