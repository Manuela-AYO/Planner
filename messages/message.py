from abc import ABC, abstractmethod


class Message(ABC):
    """
    Interface messages to the personal assistant should implement.
    """

    @abstractmethod
    def send_message(self, message) -> None:
        pass

    @abstractmethod
    def get_new_message(self) -> None:
        pass