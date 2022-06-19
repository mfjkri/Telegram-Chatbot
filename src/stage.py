from abc import (ABC, abstractmethod)
from typing import (Any, Callable, Dict, List, Union)


from telegram import (CallbackQuery, InlineKeyboardButton,
                      InlineKeyboardMarkup, ParseMode, ReplyMarkup, Update)
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, CallbackContext, Filters)

import utils.utils as utils
from user import (UserManager, User)

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


class EndConversation(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self) -> None:
        return super().setup()

    def init_users_data(self) -> None:
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        if user:
            user.logger.info("USER_REACHED_END_OF_CONVERSATION",
                             f"User:{user.chatid} has reached the end of the conversation")
        else:
            self.bot.logger.info("UNREGISTERED_USER_END_OF_CONVERSATION",
                                 f"Unregistered or banned user has reached the end of the conversation")

        self.bot.end_of_chatbot(update, context)
        return ConversationHandler.END

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)


class LetUserChoose(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self, choice_label: str,
              choice_text: str,
              choices: List[Dict[str, str]],
              choices_per_row: Union[int, None]) -> None:

        callbacks = []
        self.choice_text = choice_text
        self.keyboard = [[]]

        for idx, choice in enumerate(choices):
            def callback_wrapper(update: Update, context: CallbackContext,
                                 choice: Dict[str, Union[str, Callable]] = choice) -> USERSTATE:
                query = update.callback_query
                query.answer()
                return choice["callback"](update, context)

            if choices_per_row and idx % choices_per_row == 0:
                self.keyboard.append([])
            callbacks.append(CallbackQueryHandler(
                callback_wrapper, pattern=f"^{choice_label}:choice:{idx}$", run_async=True))
            self.keyboard[-1].append(InlineKeyboardButton(choice["text"],
                                                          callback_data=f"{choice_label}:choice:{idx}"))

        self._states = {
            choice_label + "confirmation": callbacks
        }
        self.states = self.bot.register_stage(self)
        self.CHOICE_CONFIRMATION = self.bot.unpack_states(self.states)[0]

    def init_users_data(self) -> None:
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        self.bot.edit_or_reply_message(
            update, context,
            self.choice_text,
            reply_markup=InlineKeyboardMarkup(self.keyboard)
        )
        return self.CHOICE_CONFIRMATION

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)


class GetInputFromUser(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self,
              input_label: str,
              input_text: str,
              input_handler: Callable,
              exitable: bool = False) -> None:

        self.input_text = input_text
        self.input_handler = input_handler
        self.exitable = exitable

        self.debounce = True

        self._states = {
            input_label + "message_handler": [
                MessageHandler(Filters.all, self.message_handler, run_async=True)]
        }
        self.states = self.bot.register_stage(self)
        self.INPUT_MESSAGE_HANDLER = self.bot.unpack_states(self.states)[0]

    def init_users_data(self) -> None:
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        self.bot.edit_or_reply_message(
            update, context,
            self.input_text
        )

        self.debounce = False
        return self.INPUT_MESSAGE_HANDLER

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)

    def message_handler(self, update: Update, context: CallbackContext) -> USERSTATE:
        if not self.debounce and update.message:
            self.debounce = True
            if utils.format_input_str(update.message.text, False, "/cancel") == "/cancel" and self.exitable:
                return self.bot.exit_conversation(update, context)
            else:
                return self.input_handler(update.message.text, update, context)
