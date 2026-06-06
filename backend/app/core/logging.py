import logging
import json
import sys
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any

# ContextVar to hold the trace_id for the current request context
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "log_level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get()
        }
        
        # Include extra attributes if passed via extra={}
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields) # type: ignore
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, default=str)

def setup_logging(level: int = logging.INFO) -> None:
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Standard output handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

# Setup on module load
setup_logging()
logger = logging.getLogger("quantyfin")
