# shebang
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

LOG_FILE = os.path.join("logs", f"example:base_main.log")

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

    fruits = [
        {"icon": "🍎", "name": "apple"},
        {"icon": "🍐", "name": "pear"},
        {"icon": "🍊", "name": "orange"},
        {"icon": "🍇", "name": "grape"},
        {"icon": "🍑", "name": "peach"},
        {"icon": "🍌", "name": "banana"},

    ]
    choices = [
        {
            "text": "None of the above.",
            "callback": lambda update, context: see_user_choice("none", update, context)
        }
    ]
    for fruit in fruits:
        choices.insert(
            0, {
                "text": fruit["icon"],
                "callback": lambda update, context, name=fruit["name"]: see_user_choice(name, update, context)
            })

    bot.let_user_choose(
        choice_label="fruit",
        choice_text="Which is your favorite fruit?",
        choices=choices,
        choices_per_row=3
    )
    bot.set_first_stage(stage_id=STAGE_FAV_FRUIT)
    # ---------------------------------------------------------------------------- #

    # -------------------------------- Stage: end -------------------------------- #
    bot.make_end_stage(
        stage_id=STAGE_END,
        goodbye_message="You have exited the conversation. \n\nUse /start to begin a new one.",
        reply_message=True
    )
    # ---------------------------------------------------------------------------- #

    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")

    bot.start(live_mode=LIVE_MODE)


if __name__ == "__main__":
    main()
