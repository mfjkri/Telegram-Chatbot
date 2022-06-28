from typing import (List, Dict, Union, Callable)
from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (CallbackContext, CallbackQueryHandler)

from constants import USERSTATE
from user import User
from stage import Stage

FRUITS = {
    "apple": "🍎",
    "pear": "🍐",
    "orange": "🍊",
    "grape": "🍇",
    "peach": "🍑",
    "banana": "🍌",
}


class FavoriteFruits(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        super().__init__(stage_id, next_stage_id, bot)

    def setup(self) -> None:
        self.init_users_data()

        self.states = {
            "MENU": {
                CallbackQueryHandler(
                    self.update_choice, pattern="^fruit_update_choice$"),
                CallbackQueryHandler(
                    self.stage_exit, pattern="^fruit_decline_update$"),
            },
        }

        self.bot.register_stage(self)
        self.MENU = list(self.states.values())[0]

        choices: List[Dict[str, Union[Callable, str]]] = [
            {
                "text": "None of the above.",
                "callback": lambda update, context: self.handle_user_choice("none", update, context)
            }
        ]
        for fruit, icon in FRUITS.items():
            choices.insert(
                0, {
                    "text": icon,
                    "callback": lambda update, context, name=fruit: self.handle_user_choice(name, update, context)
                })
        self.LET_USER_CHOOSE_FRUIT = self.bot.let_user_choose(
            choice_label="favorite_fruit",
            choice_text="Which is your favorite fruit?",
            choices=choices,
            choices_per_row=2
        )

    def init_users_data(self) -> None:
        self.user_manager.add_data_field("favorite_fruit", "")
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        return self.load_menu(update, context)

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)

    def load_menu(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")

        current_favorite_fruit: str = user.data.get("favorite_fruit", "")

        if current_favorite_fruit:
            menu_msg = ""
            keyboard = []

            if current_favorite_fruit != "none":
                menu_msg = f"Is your favorite fruit still: {FRUITS[current_favorite_fruit]}"
                keyboard = [
                    [InlineKeyboardButton(
                        "Yes", callback_data="fruit_decline_update")],
                    [InlineKeyboardButton(
                        "No", callback_data="fruit_update_choice")]
                ]
            else:
                menu_msg = "Have you decided on a favorite fruit yet?"
                keyboard = [
                    [InlineKeyboardButton(
                        "Yes", callback_data="fruit_update_choice")],
                    [InlineKeyboardButton(
                        "No", callback_data="fruit_decline_update")]
                ]

            self.bot.edit_or_reply_message(
                update, context,
                text=menu_msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return self.MENU
        else:
            return self.bot.proceed_next_stage(
                current_stage_id=self.stage_id,
                next_stage_id=self.LET_USER_CHOOSE_FRUIT,
                update=update, context=context
            )

    def update_choice(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.LET_USER_CHOOSE_FRUIT,
            update=update, context=context
        )

    def handle_user_choice(self, fruit_selected: str, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")

        user.update_user_data("favorite_fruit", fruit_selected)

        return self.stage_entry(update, context)
