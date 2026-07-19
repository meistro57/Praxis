import os
import logging
import logging.handlers
import json
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs in JSON format."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        # Add extra fields if present
        if hasattr(record, "run_id"):
            log_entry["run_id"] = getattr(record, "run_id")
        if hasattr(record, "candidate_id"):
            log_entry["candidate_id"] = getattr(record, "candidate_id")
        if hasattr(record, "protocol_id"):
            log_entry["protocol_id"] = getattr(record, "protocol_id")
        if hasattr(record, "latency"):
            log_entry["latency"] = getattr(record, "latency")
        if hasattr(record, "retry_count"):
            log_entry["retry_count"] = getattr(record, "retry_count")
        
        # Add exception info if any
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging(
    log_level: str = "INFO",
    log_json: bool = False,
    log_file_path: str = "logs/praxis.log"
) -> None:
    """Configures the logging system with console and rotating file handlers."""
    # Ensure logs directory exists
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    
    # Set logging level (parsed safely)
    level_num = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level_num)

    # Clean existing handlers
    root_logger.handlers = []

    # Choose formatter
    if log_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level_num)
    root_logger.addHandler(console_handler)

    # Rotating File Handler
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level_num)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up rotating file logging: {e}")
