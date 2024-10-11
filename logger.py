import logging
from logging.handlers import TimedRotatingFileHandler


logger = logging.getLogger(__name__)
_log_format = f"%(asctime)s - [%(levelname)s] - %(filename)s - %(message)s"
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("youtube_api_log.log", when='midnight', backupCount=10)
handler.setFormatter(logging.Formatter(_log_format))
logger.addHandler(handler)