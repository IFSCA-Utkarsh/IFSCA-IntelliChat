import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecureInteractionLogger:
    def __init__(self, log_dir: str = "backend/data/secure", retention_days: int = 30):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = timedelta(days=retention_days)

    def _get_log_file(self) -> Path:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"chat_logs_{today}.jsonl"

    async def log_interaction(self, entry: Dict[str, Any]):
        """Async append to JSONL file."""
        try:
            file_path = self._get_log_file()
            line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
            await asyncio.to_thread(file_path.write_text, line, encoding="utf-8", errors="ignore")  # Added errors=ignore for robustness
            # Use append mode
            with open(file_path, 'a', encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.error(f"Logging failed: {e}")

    def cleanup_old_logs(self):
        cutoff = datetime.utcnow() - self.retention_days
        for log_file in self.log_dir.glob("chat_logs_*.jsonl"):
            try:
                file_date = datetime.strptime(log_file.stem.split("_")[-1], "%Y-%m-%d")
                if file_date < cutoff:
                    log_file.unlink()
                    logger.info(f"Cleaned old log: {log_file}")
            except Exception:
                pass

interaction_logger = SecureInteractionLogger()