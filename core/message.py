from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

IGNORE_MESSAGE = "IGNORE_MESSAGE"

@dataclass
class Message:
    content: str
    sender: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class AgentResponse:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    raw_response: Any = None  # Store the original provider response
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value with default"""
        return self.metadata.get(key, default)
