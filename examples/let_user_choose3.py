#!/usr/bin/env python3
import sys

sys.path.append("src")

import logging
import os

from telegram import Update
from telegram.ext import CallbackContext

from constants import USERSTATE
from bot import Bot
from user import UserManager, User
from utils import utils
from utils.log import Log

LOG_FILE = os.path.join("logs", f"example:let_user_choose3.log")

CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
assert CONFIG, "Failed to load config.yaml. Fatal error, please remedy."\
    "\n\nLikely an invalid format."

LIVE_MODE = CONFIG["RUNTIME"]["LIVE_MODE"]
BOT_TOKEN = CONFIG["BOT_TOKENS"]["LIVE"] if LIVE_MODE else CONFIG["BOT_TOKENS"]["TEST"]


def main():
    logger = Log(
        name=__name__,
        stream_handle=sys.stdout,
        file_handle=LOG_FILE,
        log_level=logging.DEBUG
    )

    user_manager = UserManager()
    user_manager.init(logger=logger)

    bot = Bot()
    bot.init(token=BOT_TOKEN,
             logger=logger,
             config=CONFIG)

    STAGE_FAV_FRUIT = "choose:fruit"
    STAGE_FAV_SHAPE = "choose:shape"
    STAGE_END = "end"

    # --------------------------- Stage: choose:fruit --------------------------- #
    def handler_fruit_choice(choice: str, update: Update, context: CallbackContext) -> USERSTATE:
        print(f"User has selected: {choice}")

        user: User = context.user_data.get("user")
        user.update_user_data("favorite_fruit", choice)

        return bot.proceed_next_stage(
            current_stage_id=STAGE_FAV_FRUIT,
            next_stage_id=STAGE_FAV_SHAPE,
            update=update, context=context
        )

    bot.let_user_choose(
        choice_label="fruit",
        choice_text="Which is your favorite fruit?",
        choices=[
            {
                "text": "🍎",
                "callback": lambda update, context: handler_fruit_choice("apple", update, context)
            },
            {
                "text": "🍐",
                "callback": lambda update, context: handler_fruit_choice("pear", update, context)
            },
            {
                "text": "🍊",
                "callback": lambda update, context: handler_fruit_choice("orange", update, context)
            }
        ]
    )
    bot.set_first_stage(stage_id=STAGE_FAV_FRUIT)
    # ---------------------------------------------------------------------------- #

    # ---------------------------- Stage: choose:shape --------------------------- #
    def handler_shape_choice(choice: str, update: Update, context: CallbackContext) -> USERSTATE:
        print(f"User has selected: {choice}")

        user: User = context.user_data.get("user")
        user.update_user_data("favorite_shape", choice)

        return bot.proceed_next_stage(
            current_stage_id=STAGE_FAV_SHAPE,
            next_stage_id=STAGE_END,
            update=update, context=context
        )

    bot.let_user_choose(
        choice_label="shape",
        choice_text="Which is your favorite shape?",
        choices=[
            {
                "text": "🟧",
                "callback": lambda update, context: handler_shape_choice("square", update, context)
            },
            {
                "text": "🔻",
                "callback": lambda update, context: handler_shape_choice("triangle", update, context)
            },
            {
                "text": "🟢",
                "callback": lambda update, context: handler_shape_choice("circle", update, context)
            }
        ]
    )
    # ---------------------------------------------------------------------------- #

    # -------------------------------- Stage: end -------------------------------- #
    def display_favorites(update: Update, context: CallbackContext):
        user: User = context.user_data.get("user")
        fav_fruit_chosen: str = user.data.get("favorite_fruit")
        fav_shape_chosen: str = user.data.get("favorite_shape")
        bot.edit_or_reply_message(
            update, context,
            text=f"Your favorite fruit was: <b>{fav_fruit_chosen}</b>.\n"
            f"Your favorite shape was: <b>{fav_shape_chosen}</b>.\n\n"
            "You have exited the conversation.\nUse /start to begin a new one.",
        )

    bot.make_end_stage(
        stage_id=STAGE_END,
        final_callback=display_favorites
    )
    # ---------------------------------------------------------------------------- #

    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")

    bot.start(live_mode=LIVE_MODE)


if __name__ == "__main__":
    main()
