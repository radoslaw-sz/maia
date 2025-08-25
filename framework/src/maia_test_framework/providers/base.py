# maia_test_framework/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, List
from maia_test_framework.core.message import Message

class BaseProvider(ABC):
    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    async def generate(self, history: List[Message], system_message: str = "", ignore_trigger_prompt: str = ""):
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass