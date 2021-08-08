import logging


def init_logger():
    client_logger = logging.getLogger("client")
    client_logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    fh = logging.FileHandler("client.log")
    ch.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [client_side:%(module)s:%(funcName)s:L%(lineno)d] %(message)s"
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    client_logger.addHandler(ch)
    client_logger.addHandler(fh)
    return client_logger


client_logger = init_logger()
