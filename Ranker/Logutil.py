import logging

logger = None


def set_console_logging(level, logger):
    """
    :param level:
    :return:
    """
    log_formatter = logging.Formatter('[%(levelname)s]: %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)
    logger.propagate = False


def set_file_logging(log_file, logger):

    log_formatter = logging.Formatter('[%(levelname)s]:[%(filename)s %(lineno)d]:'
                                      ' %(message)s')

    fh = logging.FileHandler(log_file)
    fh.setFormatter(log_formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)


def init_logger(log_file):
    """
    init logger object
    :param log_file:
    :return:
    """
    global logger
    logger = logging.getLogger("ranking")
    set_console_logging(logging.INFO, logger)
    set_file_logging(log_file, logger)


def get_logger():
    """

    :param log_file:
    :return:
    """
    global logger
    if logger is None:
        print("Logger is not initialized call init_logger")
        return None

    return logger

