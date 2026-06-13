import re
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str
    source: str
    raw_line: str

class LogProcessor:
    def __init__(self, levels_to_ingest: List[str]):
        self.levels_to_ingest = levels_to_ingest
        # Exemple: "2023-10-01 12:00:00,123 - INFO - [app] - [source] - Log message"
        self.log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s*-\s*(\w+)\s*-\s*\[([^\]]+)\]\s*-\s*\[([^\]]+)\]\s*(.*)'
        )
    
    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        line = line.strip()
        if not line:
            return None
        
        match = self.log_pattern.match(line)
        if not match:
            return None
        
        timestamp_str, level, logger, service, message = match.groups()
        
        if level not in self.levels_to_ingest:
            return None
        
        return LogEntry(
            timestamp=timestamp_str,
            level=level,
            message=message.strip(),
            source=f"{logger}/{service}",
            raw_line=line
        )
    
    
    def should_process(self, log_entry: LogEntry) -> bool:
        return log_entry.level in self.levels_to_ingest