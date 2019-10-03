import argparse, os
from functools import partial
from bokeh.server.server import Server
from .dashmd import create_doc
from .version import __version__

def main():
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
    parser.add_argument("--title", type=str, default="DashMD", metavar="STR",
        help="Title displayed on the HTML document")
    parser.add_argument("-d", "--default-dir", type=str, default=current_dir,
        metavar="STR", help="Path to the directory containing mdin and mdout files")
    parser.add_argument("--update", type=int, default=10,
        metavar="INT", help="Idle time between each update, in seconds")


    # Parse arguments from command line
    args = parser.parse_args()
    kwargs = {
        'port': args.port,
        'allow_websocket_origin': [f'localhost:{args.port}'],
        'num_procs': 1,
    }
    # start the server
    server = Server(partial(create_doc,
        title=args.title, default_dir=args.default_dir, update=args.update,
        ), **kwargs)
    server.start()
    print(f"Opening {args.title} on http://localhost:{args.port}")
    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()
