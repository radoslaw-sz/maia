from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import uuid

IGNORE_MESSAGE = "IGNORE_MESSAGE"

@dataclass
class Message:
    content: str
    sender: str
    sender_type: str
    receiver: Optional[str] = None
    receiver_type: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self):
        return {
            "content": self.content,
            "sender": self.sender,
            "sender_type": self.sender_type,
            "receiver": self.receiver,
            "receiver_type": self.receiver_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "message_id": self.message_id
        }

@dataclass
class AgentResponse:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    raw_response: Any = None  # Store the original provider response
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value with default"""
        return self.metadata.get(key, default)
