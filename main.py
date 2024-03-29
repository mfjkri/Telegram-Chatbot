#!/usr/bin/env python3
import sys

sys.path.append("src")

import logging
import os
import shutil
from typing import Union

from telegram import Update
from telegram.ext import CallbackContext

from constants import (USERSTATE, MESSAGE_DIVIDER)
from bot import Bot
from user import (UserManager, User)
from utils import utils
from utils.log import Log
from stages.admin import AdminConsole
from stages.authenticate import Authenticate
from stages.guardian import Guardian
from stages.ctf import Ctf

LOG_FILE = os.path.join("logs", f"main.log")

CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
assert CONFIG, "Failed to load config.yaml. Fatal error, please remedy."\
    "\n\nLikely an invalid format."

LIVE_MODE = CONFIG["RUNTIME"]["LIVE_MODE"]
FRESH_START = CONFIG["RUNTIME"]["FRESH_START"] if not LIVE_MODE else False
BOT_TOKEN = CONFIG["BOT_TOKENS"]["LIVE"] if LIVE_MODE else CONFIG["BOT_TOKENS"]["TEST"]


def main():

    setup()

    # Main application logger
    logger = Log(
        name=__name__,
        stream_handle=sys.stdout,
        file_handle=LOG_FILE,
        log_level=logging.DEBUG
    )

    user_manager = UserManager()
    user_manager.init(
        logger=logger,
        log_user_logs_to_app_logs=("LOG_USER_TO_APP_LOGS" in CONFIG
                                   and CONFIG["LOG_USER_TO_APP_LOGS"]))

    bot = Bot()
    bot.init(token=BOT_TOKEN,
             logger=logger,
             config=CONFIG)

    # Bot flow:
    #   admin -> authenticate -> info_collect_username -> choose_disclaimer -> guardian -> ctf -> end
    #   admin stage is automatically skipped if user is not admin
    STAGE_ADMIN = "admin"
    STAGE_AUTHENTICATE = "authenticate"
    STAGE_COLLECT_USERNAME = "info_collect_username"
    STAGE_DISCLAIMER = "choose_disclaimer"
    STAGE_GUARDIAN = "guardian"
    STAGE_CTF = "ctf"
    STAGE_END = "end"

    # ------------------------------- Stage: admin ------------------------------- #
    admin: AdminConsole = AdminConsole(
        stage_id=STAGE_ADMIN,
        next_stage_id=STAGE_AUTHENTICATE,
        bot=bot
    )
    admin.setup()
    bot.set_first_stage(STAGE_ADMIN)
    # ---------------------------------------------------------------------------- #

    # ---------------------------- Stage: authenticate --------------------------- #
    authenticate: Authenticate = Authenticate(
        stage_id=STAGE_AUTHENTICATE,
        next_stage_id=STAGE_COLLECT_USERNAME,
        bot=bot
    )
    authenticate.setup()
    # ---------------------------------------------------------------------------- #

    # ----------------------- Stage: info_collect_username ----------------------- #
    def format_name_input(input_str: Union[str, bool]):
        if input_str is not True:
            return utils.format_input_str(input_str, True)
        elif input_str is True:
            return "Only alphanumeric characters"

    bot.get_user_info(
        stage_id=STAGE_COLLECT_USERNAME,
        next_stage_id=STAGE_DISCLAIMER,
        data_label="username",
        input_formatter=format_name_input,
        additional_text="This is the name displayed on the leaderboard.",
        allow_update=True
    )
    # ---------------------------------------------------------------------------- #

    # ------------------------- Stage: choose_disclaimer ------------------------- #
    disclaimer_text = "<b><u>DISCLAIMER</u></b>\n\n"\
                      "- This Telegram Chatbot is just a medium for submission of answers.\n"\
                      "- Do not attack or DoS the Telegram Chatbot.\n"\
                      "- Read about the <u>Computer Misuse and Cybersecurity Act</u> <a href='https://sso.agc.gov.sg//Act/CMA1993'>here</a>.\n\n"\
                      f"{MESSAGE_DIVIDER}"\
                      "By pressing <i>Accept</i> you have read and agreed to conditions listed above."

    def accept_disclaimer(update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        user.logger.info("ACCEPTED_DISCLAIMER",
                         f"User:{user.chatid} has accepted the disclaimer.")
        return bot.proceed_next_stage(STAGE_DISCLAIMER, STAGE_GUARDIAN, update, context)

    bot.let_user_choose(
        stage_id=STAGE_DISCLAIMER,
        choice_text=disclaimer_text,
        choices=[
            {
                "text": "Accept",
                "callback": accept_disclaimer
                # "callback": lambda *args: bot.proceed_next_stage(STAGE_DISCLAIMER, STAGE_CTF, *args)
            },
        ]
    )
    # ---------------------------------------------------------------------------- #

    # ------------------------------ Stage: guardian ----------------------------- #
    guardian: Guardian = Guardian(
        stage_id=STAGE_GUARDIAN,
        next_stage_id=STAGE_CTF,
        bot=bot
    )
    guardian.setup()
    # ---------------------------------------------------------------------------- #

    # -------------------------------- Stage: ctf -------------------------------- #
    ctf: Ctf = Ctf(
        stage_id=STAGE_CTF,
        next_stage_id=STAGE_END,
        bot=bot
    )
    ctf.setup()
    # ---------------------------------------------------------------------------- #

    # -------------------------------- Stage: end -------------------------------- #
    bot.make_end_stage(
        stage_id=STAGE_END,
        goodbye_message="You have exited the conversation. \n\nUse /start to begin a new one.",
    )
    # ---------------------------------------------------------------------------- #

    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")

    bot.start(live_mode=LIVE_MODE)


def setup():
    """
    Creates the neccesary runtime directories if missing (logs).
    If FRESH_START is True, then it will clear existing files from last run (logs/* and users/*).

    :return: None
    """
    utils.get_dir_or_create(os.path.join("logs"))
    if FRESH_START:
        users_directory = os.path.join("users")

        for chatid in os.listdir(users_directory):
            user_directory = os.path.join(users_directory, chatid)
            if os.path.isdir(user_directory):
                shutil.rmtree(user_directory)

        if os.path.isfile(LOG_FILE):
            os.remove(LOG_FILE)


if __name__ == "__main__":
    main()
