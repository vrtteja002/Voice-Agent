from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = datetime.now()


class Conversation(BaseModel):
    id: str
    call_sid: str
    phone_number: str
    messages: List[Message] = []
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    context: Dict[str, Any] = {}