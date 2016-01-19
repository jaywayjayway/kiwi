import os
import sys
import logging
import logging.handlers
loggers = {}
log_dir = "/var/log/kiwi"

def iter_lines(fd, chunk_size=1024):
    '''Iterates over the content of a file-like object line-by-line.'''

    pending = None

    while True:
        chunk = os.read(fd.fileno(), chunk_size)
        if not chunk:
            break

        if pending is not None:
            chunk = pending + chunk
            pending = None

        lines = chunk.splitlines()

        if lines and lines[-1]:
            pending = lines.pop()

        for line in lines:
            yield line

    if pending:
        yield(pending)



def create_logger(name, filename):
    root = logging.getLogger(name)
    FORMAT = '[%(levelname)-8s] [%(asctime)s] [%(name)s:%(lineno)d] %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    channel = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=100000000,
            backupCount=10)
    channel.setFormatter(logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(channel)

    #console = logging.StreamHandler()
    #console.setFormatter(logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT))
    #root.addHandler(console)
    root.setLevel(logging.DEBUG)
    return logging.getLogger(name)



def getLogger(name, filename="kiwi"):
    if not filename.endswith('.log'):
        filename += '.log'
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    loggers[name] = create_logger(name, os.path.join(log_dir, filename))
    return loggers[name]

