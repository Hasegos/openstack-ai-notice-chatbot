import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR    = "logs"
_LOG_FILE   = os.path.join(_LOG_DIR, "app.log")
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """
    루트 로거에 RotatingFileHandler + StreamHandler를 등록합니다.
    앱 기동 시 main.py에서 1회 호출하세요.
    """
    os.makedirs(_LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # 파일 핸들러 — 10MB 초과 시 롤오버, 최대 5개 보관
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # 콘솔 핸들러 — Docker 환경에서 docker logs 로 실시간 확인 가능
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)
