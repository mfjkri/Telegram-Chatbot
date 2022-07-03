#!/usr/bin/env python3
import sys

sys.path.append("src")

import logging
import os
from typing import Union

from bot import Bot
from user import UserManager
from utils import utils
from utils.log import Log

LOG_FILE = os.path.join("logs", f"example:get_user_info.log")

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

    STAGE_FAV_FRUIT = "collect:favorite_fruit"
    STAGE_END = "end"

    # ------------------------ Stage: collect:favorite_fruit ----------------------- #
    valid_fruits = ["apple", "orange", "pear", "banana", "peach", "grape"]

    def fruit_input_formatter(input_str: Union[str, bool]):
        if input_str is True:
            return '\n' +\
                ", ".join(valid_fruits)
        else:
            return input_str if input_str.lower() in valid_fruits else False

    bot.get_user_info(
        data_label="favorite_fruit",
        next_stage_id=STAGE_END,
        input_formatter=fruit_input_formatter,
        additional_text="This info will not be used to identify you.",
        use_last_saved=True, allow_update=True
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
