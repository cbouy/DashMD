import argparse, logging, os
from tornado.ioloop import IOLoop
from bokeh.application.handlers import DirectoryHandler
from bokeh.application import Application
from bokeh.server.server import Server
from bokeh.settings import settings
from dashmd.version import __version__
from dashmd.logger import loglevel, dashmd_loglevel_to_bokeh

def parse_args():
    current_dir = os.path.abspath(os.path.curdir)
    # Argparse
    parser = argparse.ArgumentParser(
        description="Monitor and visualize MD simulations from Amber in real time",
        epilog="Copyright 2019, Cédric Bouysset",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--version", action="version",
        version=f'DashMD version {__version__}', help="Show version and exit")
    parser.add_argument("--port", type=int, default=5100, metavar="INT",
        help="Port number used by the bokeh server")
    parser.add_argument("--update", type=int, default=10, metavar="INT",
        help="Update rate to check and load new data")
    parser.add_argument("--default-dir", type=str, default=".", metavar="STR",
        help="Default directory")
    parser.add_argument("--log", metavar="level", help="Set level of the logger",
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='INFO')

    # Parse arguments from command line
    args = parser.parse_args()
    return args


def main():
    # parse command line arguments
    args = parse_args()
    # set the logger
    log = logging.getLogger("dashmd")
    log.setLevel(loglevel.get(args.log))
    log.debug(f"Set log level to '{args.log}'")
    os.environ['BOKEH_PY_LOG_LEVEL'] = dashmd_loglevel_to_bokeh.get(args.log)
    os.environ['BOKEH_LOG_LEVEL'] = dashmd_loglevel_to_bokeh.get(args.log)
    log.debug(f"Set Bokeh log level to '{dashmd_loglevel_to_bokeh.get(args.log)}'")
    # start the server
    try:
        log.info("Preparing the Bokeh server")
        io_loop = IOLoop.current()
        # force bokeh to load resources from CDN
        os.environ['BOKEH_RESOURCES'] = 'cdn'
        app_dir = os.path.dirname(os.path.realpath(__file__))
        bokeh_app = Application(DirectoryHandler(filename=app_dir, argv=[args.default_dir, args.update]))
        server = Server(
            {'/': bokeh_app}, io_loop=io_loop,
            port=args.port, num_procs=1,
            allow_websocket_origin=[f'localhost:{args.port}'],
        )
    except OSError:
        log.error(f"[ERROR] Port {args.port} is already in use. Please specify a different one by using the --port flag.")
        sys.exit(1)

    server.start()
    log.info(f"Opening DashMD on http://localhost:{args.port}")
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
