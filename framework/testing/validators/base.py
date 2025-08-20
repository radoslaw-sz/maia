from abc import ABC, abstractmethod
from framework.core.session import Session

class BaseValidator(ABC):
    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def validate(self):
        pass
