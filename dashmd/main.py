#!/usr/bin/env python

import logging, sys
from bokeh.io import curdoc
from application import create_app

# parse remaining command line arguments
_, default_dir, update, port = sys.argv
# open logger
log = logging.getLogger("dashmd")
# create bokeh application
doc = curdoc()
create_app(doc, default_dir=default_dir, update=update, port=int(port))
