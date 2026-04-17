import logging
import sys

def setup_logging():
    """
    Configures a centralized, production-grade JSON or standard structured logger.
    Replaces random print() statements to ensure logs can be parsed by Datadog or ELK.
    """
    logger = logging.getLogger("jobify")
    logger.setLevel(logging.INFO)
    
    # Check if handlers exist to prevent duplicate logs in reloader
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

log = setup_logging()
