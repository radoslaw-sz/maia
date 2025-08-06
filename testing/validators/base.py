from abc import ABC, abstractmethod
from maia_test_framework.core.session import Session

class BaseValidator(ABC):
    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def validate(self):
        pass
