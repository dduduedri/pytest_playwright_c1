import logging

# shared log line format. pytest's live log (log_cli_format in pytest.ini) uses the
# same layout so console output looks consistent.
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


# return a logger for the given module/name.
#
# no handler is attached here on purpose: during test runs pytest's live log
# (`log_cli = true` in pytest.ini) streams these records to the console in real time.
# records propagate to pytest's handler, so adding our own would print every line
# twice. for use outside pytest, call logging.basicConfig() once in your entry point.
def get_logger(name: str = "framework", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
