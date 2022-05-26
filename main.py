# shebang
import sys
sys.path.append("src")

import logging
import os
import shutil

from typing import Union
from bot import MESSAGE_DIVIDER, USERSTATE, Bot, Update, CallbackContext
from user import UserManager, User
import utils.utils as utils
from utils.log import Log
from stages.admin import AdminConsole
from stages.authenticate import Authenticate
from stages.ctf import Ctf

LOG_FILE = os.path.join("logs", f"csabot.log")

CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
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
        logger, "LOG_USER_TO_APP_LOGS" in CONFIG and CONFIG["LOG_USER_TO_APP_LOGS"])

    bot = Bot()
    bot.init(BOT_TOKEN, logger)

    # Bot flow:
    #   admin -> authenticate -> collect:username -> choose:disclaimer -> CTF -> end
    #   admin stage is automatically skipped if user is not admin
    STAGE_ADMIN = "admin"
    STAGE_AUTHENTICATE = "authenticate"
    STAGE_COLLECT_USERNAME = "collect:username"
    STAGE_DISCLAIMER = "choose:disclaimer"
    STAGE_CTF = "CTF"
    STAGE_END = "end"

    # Stage admin
    admin: AdminConsole = AdminConsole(bot)
    admin.setup(
        stage_id=STAGE_ADMIN,
        next_stage_id=STAGE_AUTHENTICATE
    )

    # Stage authenticate
    authenticate: Authenticate = Authenticate(bot)
    authenticate.setup(
        stage_id=STAGE_AUTHENTICATE,
        next_stage_id=STAGE_COLLECT_USERNAME
    )

    # Stage collect:username
    def format_name_input(input_str: Union[str, bool]):
        if input_str is not True:
            return utils.format_input_str(input_str, True, "' ")
    bot.get_info_from_user(  # This stage id is collect:username
        data_label="username",
        next_stage_id=STAGE_DISCLAIMER,
        input_formatter=format_name_input,
        additional_text="This is the name displayed on the leaderboard.",
        allow_update=True
    )

    # Stage choose:disclaimer
    disclaimer_text = "<b><u>DISCLAIMER</u></b>\n\n"\
                      "- This Telegram Chatbot is just a medium for submission of answers.\n"\
                      "- Do not attack or DoS the Telegram Chatbot.\n"\
                      "- Read about the <u>Computer Misuse and Cybersecurity Act</u> <a href='https://sso.agc.gov.sg//Act/CMA1993'>here</a>.\n\n"\
                      f"{MESSAGE_DIVIDER}"\
                      "By pressing <i>Continue</i> you have read and agreed to conditions listed above."

    def accept_disclaimer(update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        user.logger.info("ACCEPTED_DISCLAIMER",
                         f"User:{user.chatid} has accepted the disclaimer.")
        return bot.proceed_next_stage(STAGE_DISCLAIMER, STAGE_CTF, update, context)
    bot.let_user_choose(    # This stage id is choose:disclaimer
        choice_label="disclaimer",
        choice_text=disclaimer_text,
        choices=[
            {
                "text": "Continue",
                "callback": accept_disclaimer
                # "callback": lambda *args: bot.proceed_next_stage(STAGE_DISCLAIMER, STAGE_CTF, *args)
            },
        ]
    )

    # Stage ctf
    ctf: Ctf = Ctf(os.path.join("ctf"), bot)
    ctf.setup(  # This stage id is CTF
        stage_id=STAGE_CTF,
        next_stage_id=STAGE_END,
    )

    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")

    # bot.set_first_stage(STAGE_ADMIN)
    bot.set_first_stage(STAGE_ADMIN)
    bot.set_end_of_chatbot(
        lambda update, context: bot.edit_or_reply_message(
            update, context, "You have exited the conversation. \n\nUse /start to begin a new one.", reply_message=True)
    )
    bot.start(live_mode=LIVE_MODE)


def setup():
    """
    Creates the neccesary runtime directories if missing (logs).
    If FRESH_START is True, then it will clear existing files (logs/* and users/*).

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
