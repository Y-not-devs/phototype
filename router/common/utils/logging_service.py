import logging
import os
import sys
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter to modify the name in log messages"""
    def format(self, record):
        if record.name.startswith("__"):
            record.name = record.name.upper()
            record.name = record.name.replace("__", "")
        elif "." in record.name:
            last_part = record.name.split(".")[-1]
            record.name = last_part[0].upper() + last_part[1:]
        else:
            record.name = record.name[0].upper() + record.name[1:]
        
        return super().format(record)

class LoggerService:
    def __init__(self, package_name, log_directory='logs', log_level=logging.INFO):
        """
        Initializes the LoggerService class
        :param package_name: Name of the logger (usually __name__)
        :param log_directory: Directory where logs will be stored
        :param log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        """
        self.package_name = package_name
        self.log_directory = log_directory
        self.log_level = log_level
        self.log_filename = os.path.join(log_directory, f"{datetime.now().strftime('%Y-%m-%d')}.log")

        # Ensure the log directory exists
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)

        # Set up the logging configuration
        self._setup_logger()

        # Set up uncaught exception logging
        self._setup_uncaught_exception_handler()

    def _setup_logger(self):
        """Sets up the logging configuration"""
        logging.basicConfig(
            level=self.log_level,
            format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.FileHandler(self.log_filename),
                logging.StreamHandler()
            ]
        )

        # Apply the custom formatter to all handlers
        for handler in logging.getLogger().handlers:
            handler.setFormatter(CustomFormatter('[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s', datefmt='%H:%M:%S'))

    def _setup_uncaught_exception_handler(self):
        """Sets up a handler for uncaught exceptions"""
        def log_uncaught_exceptions(exc_type, exc_value, exc_tb):
            if issubclass(exc_type, KeyboardInterrupt):
                self.log("info", "Bot shutdowned by Admin")
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return
            self.get_logger().error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
        
        sys.excepthook = log_uncaught_exceptions

    def get_logger(self):
        """Returns the logger instance for the specified package"""
        return logging.getLogger(self.package_name)

    def log(self, level, msg, *args, **kwargs):
        """Log a message with the given level"""
        logger = self.get_logger()
        if level == 'debug':
            logger.debug(msg, *args, **kwargs)
        elif level == 'info':
            logger.info(msg, *args, **kwargs)
        elif level == 'warning':
            logger.warning(msg, *args, **kwargs)
        elif level == 'error':
            logger.error(msg, *args, **kwargs)
        elif level == 'exception':
            logger.exception(msg, *args, **kwargs)
        elif level == 'critical':
            logger.critical(msg, *args, **kwargs)
        else:
            logger.info(msg, *args, **kwargs)