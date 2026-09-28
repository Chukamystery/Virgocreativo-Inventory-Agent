import logging


def configure_logging():
    """
    Basic application logging configuration.

    Task 11 learning version.

    Production systems would normally send
    logs to a centralized logging platform.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


def get_logger(
    name: str,
):
    return logging.getLogger(
        name
    )