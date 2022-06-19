from abc import (ABC, abstractmethod)


from telegram import Update
from telegram.ext import CallbackContext

from user import UserManager

USERSTATE = int


class Stage(ABC):
    @abstractmethod
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        from bot import Bot

        self.bot: Bot = bot
        self.user_manager: UserManager = self.bot.users_manager

        self.stage_id = stage_id
        self.next_stage_id = next_stage_id

        self.states = {}
        self._states = {}

    @abstractmethod
    def setup(self) -> None:
        self.bot.register_stage(self)

    @abstractmethod
    def init_users_data(self) -> None:
        """"""

    @abstractmethod
    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        """"""

    @abstractmethod
    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        # TODO: Route this to end the bot conversation
        """"""
