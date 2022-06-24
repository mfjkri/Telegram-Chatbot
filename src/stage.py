import time
from abc import (ABC, abstractmethod)
from typing import (Callable, Dict, List, Union, Optional)


from telegram import (InlineKeyboardButton,
                      InlineKeyboardMarkup, Update)
from telegram.ext import (ConversationHandler, CallbackQueryHandler,
                          MessageHandler, CallbackContext, Filters)

from constants import (USERSTATE, MESSAGE_DIVIDER)
from utils import utils
from user import (UserManager, User)


class Stage(ABC):
    @abstractmethod
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        """"""
        from bot import Bot

        self.bot: Bot = bot
        self.user_manager: UserManager = self.bot.user_manager

        self.stage_id = stage_id
        self.next_stage_id = next_stage_id

        self.states = {}

    @abstractmethod
    def setup(self) -> None:
        """"""
        self.init_users_data()

        self.states = {
            # "STATE_NAME" : [
            #     CallbackQueryHandler(
            #         callback, pattern=f"^$",run_async=True),
            #     CallbackQueryHandler(
            #         callback, pattern=f"^$",run_async=True),
            #     ...
            # ],
            # "STATE_NAME_2" : [
            #     MessageHandler(Filters.all, callback, run_async=True)
            # ],
            # ...
        }
        self.bot.register_stage(self)
        # self.___, self.___ = self.bot.unpack_states(self.states)

    @abstractmethod
    def init_users_data(self) -> None:
        """"""
        # self.user_manager.add_data_field("DATA_FIELD", "")
        self.users_data_initialized = True

    @abstractmethod
    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        """"""
        # return self.load_something(update, context)

    @abstractmethod
    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        """"""
        query = update.callback_query
        if query:
            query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.next_stage_id or self.bot.end_stage.stage_id,
            update=update, context=context
        )

# ---------------------------------------------------------------------------- #
# ------------------------------ In-built stages ----------------------------- #


class LetUserChoose(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self, choice_label: str,
              choice_text: str,
              choices: List[Dict[str, str]],
              choices_per_row: Optional[int]) -> None:

        self.init_users_data()

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

        self.states = {
            choice_label + "confirmation": callbacks
        }
        self.bot.register_stage(self)
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

        self.init_users_data()

        self.input_text = input_text
        self.input_handler = input_handler
        self.exitable = exitable

        self.debounce = True

        self.states = {
            input_label + "message_handler": [
                MessageHandler(Filters.all, self.message_handler, run_async=True)]
        }
        self.bot.register_stage(self)
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


class GetInfoFromUser(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self, data_label: str,
              input_formatter: Callable,
              additional_text: str,
              use_last_saved: bool,
              allow_update: bool) -> None:

        self.data_label = data_label
        self.init_users_data()

        self.input_formatter = input_formatter
        self.additional_text = additional_text
        self.use_last_saved = use_last_saved
        self.allow_update = allow_update

        self.debounce = True

        self.confirm_input_pattern = f"collect:{data_label}:confirm"
        self.retry_input_pattern = f"collect:{data_label}:retry"

        self.states = {
            data_label + "input_handler": [
                MessageHandler(Filters.all, self.input_handler, run_async=True)
            ],
            data_label + "confirmation": [
                CallbackQueryHandler(
                    self.retry_input, pattern=f"^{self.retry_input_pattern}$", run_async=True),
                CallbackQueryHandler(
                    self.confirm_input, pattern=f"^{self.confirm_input_pattern}$", run_async=True),
            ]
        }
        self.bot.register_stage(self)
        self.INPUT_HANDLER, self.INPUT_CONFIRMATION = self.bot.unpack_states(
            self.states)

    def init_users_data(self) -> None:
        self.user_manager.add_data_field(self.data_label, "")
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        saved_data = user.data.get(self.data_label)

        if saved_data and self.use_last_saved:
            if self.allow_update:
                user.logger.info("USER_DATA_INPUT_UPDATE_PROMPT",
                                 f"User:{user.chatid} is choosing whether to update input({self.data_label})")

                context.user_data.update(
                    {f"input:{self.data_label}": saved_data})

                text = f"Confirm your <b><u>{self.data_label}</u></b>:\n\n"
                text += f"<i>{self.additional_text}</i>\n\n" if self.additional_text else ""
                text += MESSAGE_DIVIDER
                text += f"<b>{saved_data}</b>\n"
                text += MESSAGE_DIVIDER

                self.bot.edit_or_reply_message(
                    update, context,
                    text=text,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                "Confirm", callback_data=self.confirm_input_pattern),
                            InlineKeyboardButton(
                                "Edit", callback_data=self.retry_input_pattern),
                        ]
                    ]),
                )

                return self.INPUT_CONFIRMATION
            else:
                user.logger.info("USER_DATA_INPUT_UPDATE_FORBIDDEN",
                                 f"User:{user.chatid} is forbidden from updating input({self.data_label}). Using old value...")
                return self.stage_exit(update, context)
        else:
            user.logger.info("USER_DATA_INPUT_INIT_PROMPT",
                             f"User:{user.chatid} is choosing input({self.data_label})")
            self.bot.edit_or_reply_message(
                update, context,
                text=f"Please enter your <b>{self.data_label}</b>:" +
                (f"\n\n<i>{self.additional_text}</i>" if self.additional_text else " ")
            )
            self.debounce = False
            return self.INPUT_HANDLER

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.next_stage_id,
            update=update, context=context
        )

    def input_handler(self, update: Update, context: CallbackContext) -> USERSTATE:

        if not self.debounce and update.message is not None:
            self.debounce = True

            user: User = context.user_data.get("user")

            user_input = update.message.text
            formatted_user_input = self.input_formatter(user_input)

            if user_input == "cancel":
                return self.bot.exit_conversation(
                    current_stage_id=self.stage_id,
                    update=update, context=context
                )
            # elif user_input == "/start":
                # return self.proceed_next_stage(stage_id, None, update, context)

            if formatted_user_input:
                user.logger.info("USER_DATA_INPUT_CONFIRMATION",
                                 f"User:{user.chatid} entered an input({self.data_label}) of @{user_input}@")

                context.user_data.update(
                    {f"input:{self.data_label}": formatted_user_input})

                self.bot.edit_or_reply_message(
                    update, context,
                    text=f"Is your {self.data_label}: <b>{formatted_user_input}</b>?",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                "Confirm", callback_data=self.confirm_input_pattern),
                            InlineKeyboardButton(
                                "Edit", callback_data=self.retry_input_pattern),
                        ]
                    ])
                )

                return self.INPUT_CONFIRMATION
            else:
                user.logger.warning("USER_DATA_INPUT_WRONG_FORMAT",
                                    f"User:{user.chatid} entered an input({self.data_label}) of the wrong format. @{user_input}@")

                text = f"Your input: <b>{user_input}</b> is invalid."
                expected_input_format = self.input_formatter(True)
                if expected_input_format is not True:
                    text += f"\n\nExpected format: {expected_input_format}"

                self.bot.edit_or_reply_message(
                    update, context,
                    text=text
                )
                return self.prompt_entry(update, context)

    def confirm_input(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        user.logger.info("USER_DATA_INPUT_CONFIRMED",
                         f"User:{user.chatid} confirmed an input({self.data_label})")
        user.update_user_data(
            self.data_label, context.user_data[f"input:{self.data_label}"])

        # If we are already removing buttons, then there
        # is no need to have an extra visual delay
        # to make the change obvious
        if not self.bot.behavior_remove_inline_markup:
            self.bot.edit_or_reply_message(
                update, context,
                "💭 Loading..."
            )
            time.sleep(0.25)

        return self.stage_exit(update, context)

    def retry_input(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        user.logger.info("USER_DATA_INPUT_RETRY",
                         f"User:{user.chatid} retrying an input({self.data_label})")

        self.bot.edit_or_reply_message(
            update, context,
            f"Please enter your <b>{self.data_label}</b>:"
        )
        self.debounce = False
        return self.INPUT_HANDLER


class EndConversation(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self,
              goodbye_message: Optional[str] = "",
              reply_message: bool = True) -> None:
        self.goodbye_message = goodbye_message
        self.reply_message = reply_message
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

        if self.goodbye_message:
            self.bot.edit_or_reply_message(
                update, context,
                text=self.goodbye_message,
                reply_message=self.reply_message)
        return ConversationHandler.END

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)
