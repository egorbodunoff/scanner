import logging


def get_base_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler('cache.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    file_formatter = '\t%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s'
    file_handler.setFormatter(logging.Formatter(file_formatter))

    return logger


def get_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    stdout_formatter = 'stdout_log\t%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s'
    stream_handler.setFormatter(logging.Formatter(stdout_formatter))

    return stream_handler


logger = get_base_logger()