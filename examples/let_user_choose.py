#!/usr/bin/env python3
import sys

sys.path.append("src")

import logging
import os

from telegram import Update
from telegram.ext import CallbackContext

from constants import USERSTATE
from bot import Bot
from user import UserManager
from utils import utils
from utils.log import Log

LOG_FILE = os.path.join("logs", f"example:let_user_choose.log")

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
    STAGE_END = "end"

    # --------------------------- Stage: choose:fruit --------------------------- #
    def see_user_choice(choice: str, update: Update, context: CallbackContext) -> USERSTATE:
        print(f"User has selected: {choice}")
        if choice != "none":
            return bot.proceed_next_stage(
                current_stage_id=STAGE_FAV_FRUIT,
                next_stage_id=STAGE_FAV_FRUIT,
                update=update, context=context
            )
        else:
            return bot.proceed_next_stage(
                current_stage_id=STAGE_FAV_FRUIT,
                next_stage_id=STAGE_END,
                update=update, context=context
            )

    bot.let_user_choose(
        choice_label="fruit",
        choice_text="Which is your favorite fruit?",
        choices=[
            {
                "text": "🍎",
                "callback": lambda update, context: see_user_choice("apple", update, context)
            },
            {
                "text": "🍐",
                "callback": lambda update, context: see_user_choice("pear", update, context)
            },
            {
                "text": "🍊",
                "callback": lambda update, context: see_user_choice("orange", update, context)
            },
            {
                "text": "🍇",
                "callback": lambda update, context: see_user_choice("grape", update, context)
            },
            {
                "text": "None of the above.",
                "callback": lambda update, context: see_user_choice("none", update, context)
            }
        ],
        choices_per_row=2
    )
    bot.set_first_stage(stage_id=STAGE_FAV_FRUIT)
    # ---------------------------------------------------------------------------- #

    # -------------------------------- Stage: end -------------------------------- #
    bot.make_end_stage(
        stage_id=STAGE_END,
        goodbye_message="You have exited the conversation. \n\nUse /start to begin a new one."
    )
    # ---------------------------------------------------------------------------- #

    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")

    bot.start(live_mode=LIVE_MODE)


if __name__ == "__main__":
    main()
