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

LOG_FILE = os.path.join("logs", f"example:get_user_info2.log")

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

    STAGE_COLLECT_EMAIL = "info_collect_email"
    STAGE_END = "end"

    # -------------------- Stage: info_collect_favorite_fruit -------------------- #
    def format_email_input(input_str: Union[str, bool]):
        if input_str is True:
            return "example@domain.com"
        else:
            input_str = utils.format_input_str(input_str, True, "@.")
            return utils.check_if_valid_email_format(input_str)

    bot.get_user_info(
        stage_id=STAGE_COLLECT_EMAIL,
        next_stage_id=STAGE_END,
        data_label="email",
        input_formatter=format_email_input,
        additional_text=None,
        allow_update=True
    )
    bot.set_first_stage(stage_id=STAGE_COLLECT_EMAIL)
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
