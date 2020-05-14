import logging


def init():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )
