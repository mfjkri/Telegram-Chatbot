from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from constants import USERSTATE
from stage import Stage


class BasicStage(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        super().__init__(stage_id, next_stage_id, bot)

    def setup(self) -> None:
        self.init_users_data()

        self.states = {
            "MENU": [
                CallbackQueryHandler(
                    self.stage_exit, pattern="^basic_exit_stage$"),
                CallbackQueryHandler(
                    self.print_message, pattern="^basic_print_message$"),
            ]
        }
        self.bot.register_stage(self)
        # USERSTATES
        (self.MENU,) = self.unpacked_states

    def init_users_data(self) -> None:
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        return self.load_menu(update, context)

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)

    def load_menu(self, update: Update, context: CallbackContext) -> USERSTATE:
        self.bot.edit_or_reply_message(
            update, context,
            f"Welcome to Basic Stage",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Print My Name", callback_data="basic_print_message")
                    ],
                    [
                        InlineKeyboardButton(
                            "Exit", callback_data="basic_exit_stage")
                    ]
                ]
            ),
            reply_message=True
        )

        return self.MENU

    def print_message(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        self.bot.edit_or_reply_message(
            update, context,
            f"Your name is {query.from_user.full_name}"
        )

        return self.load_menu(update, context)
