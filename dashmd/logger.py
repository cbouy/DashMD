import logging

logging.basicConfig(format='%(levelname)-8s [%(asctime)s] %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger("dashmd")

loglevel = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}

dashmd_loglevel_to_bokeh = {
    'CRITICAL': 'fatal',
    'ERROR': 'error',
    'WARNING': 'warn',
    'INFO': 'info',
    'DEBUG': 'debug',
}
