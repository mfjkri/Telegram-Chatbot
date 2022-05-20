# shebang
import sys
sys.path.append("src")

import logging
import os
import shutil

from typing import Union
from bot import MESSAGE_DIVIDER, Bot
from user import Users
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

    logger = Log(
        name=__name__,
        stream_handle=sys.stdout,
        file_handle=LOG_FILE,
        log_level=logging.DEBUG
    )

    users = Users()
    users.init(
        logger, "LOG_USER_TO_APP_LOGS" in CONFIG and CONFIG["LOG_USER_TO_APP_LOGS"])

    bot = Bot()
    bot.init(BOT_TOKEN, logger)

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
    bot.let_user_choose(    # This stage id is choose:disclaimer
        choice_label="disclaimer",
        choice_text=disclaimer_text,
        choices=[
            {
                "text": "Continue",
                "callback": lambda *args: bot.proceed_next_stage(
                    STAGE_DISCLAIMER,
                    STAGE_CTF,
                    *args
                )
            },
        ]
    )

    # Stage ctf
    ctf: Ctf = Ctf(os.path.join(os.getcwd(), "ctf"), bot)
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
            update, context, "You have exited the conversation. \n\nUse /start to begin a new one.")
    )
    bot.start(live_mode=LIVE_MODE)


def setup():
    utils.get_dir_or_create(os.path.join(os.getcwd(), "logs"))
    if FRESH_START:
        users_directory = os.path.join(os.getcwd(), "users")

        for chatid in os.listdir(users_directory):
            user_directory = os.path.join(users_directory, chatid)
            if os.path.isdir(user_directory):
                shutil.rmtree(user_directory)

        if os.path.isfile(LOG_FILE):
            os.remove(LOG_FILE)


if __name__ == "__main__":
    main()


# def for_reference():
#     STAGE_COLLECT_NAME = "collect:name"
#     STAGE_COLLECT_PHONENUMBER = "collect:phone number"
#     STAGE_COLLECT_EMAIL = "collect:email"
#     STAGE_GUARDIAN = "guardian"
#     STAGE_ENTER_CTF = "choose:enter_ctf"


#     # Stage collect:name
#     def format_name_input(input_str : Union[str, bool]):
#         if input_str is not True:
#             return utils.format_input_str(input_str, True, "' ")
#     bot.get_info_from_user( # This stage id is collect:name
#         data_label="name",
#         next_stage_id=STAGE_COLLECT_PHONENUMBER,
#         input_formatter=format_name_input,
#         allow_update=True
#     )


#     # Stage collect:phone number
#     def format_number_input(input_str : Union[str, bool]):
#         if input_str is True:
#             return "91234567"
#         else:
#             if input_str.find("+65") >= 0:
#                 input_str = input_str[3:]
#             input_str = utils.format_input_str(input_str, False, "0123456789")
#             return input_str if (
#                 len(input_str) == 8 and "689".find(input_str[0]) >= 0
#             ) else False
#     bot.get_info_from_user( # This stage id is collect:phone number
#         data_label="phone number",
#         next_stage_id=STAGE_COLLECT_EMAIL,
#         input_formatter=format_number_input,
#         additional_text="⚠ We will only use this to contact prize winners.",
#         allow_update=True
#     )


#     # Stage collect:email
#     def format_email_input(input_str : Union[str, bool]):
#         if input_str is True:
#             return "example@domain.com"
#         else:
#             input_str = utils.format_input_str(input_str, True, "@.")
#             return utils.check_if_valid_email_format(input_str)
#     bot.get_info_from_user( # This stage id is collect:email
#         data_label="email",
#         next_stage_id=STAGE_GUARDIAN,
#         input_formatter=format_email_input,
#         additional_text=None, #"⚠ This will be the only channel that we use to contact or share opportunities via.",
#         allow_update=True
#     )


#     # Stage guardian
#     guardian : Guardian = Guardian(bot)
#     guardian.setup( # This stage id is guardian
#         stage_id=STAGE_GUARDIAN,
#         next_stage_id=STAGE_ENTER_CTF
#     )


#     # Stage enter_ctf
#     stage4_choice_text = "Want to win a prize 🎁?\n\n"
#     stage4_choice_text += "Take part in the Capture the Flag (CTF) Challenge and win a prize if you top the leaderboard!\n\n"
#     stage4_choice_text += "<i>Note:\n📞 The winner will be contacted via phone call at the end of the session.</i>"
#     # stage4_choice_text += "<i>\nIn the event of a tie, the person who obtained the score first is the winner.</i>"
#     bot.let_user_choose( # This stage id is choose:enter_ctf
#         choice_label="enter_ctf",
#         choice_text=stage4_choice_text,
#         choices=[
#             {
#                 "text" : "I'm in!",
#                 "callback" : lambda *args : bot.proceed_next_stage(
#                     STAGE_ENTER_CTF,
#                     STAGE_CTF,
#                     *args
#                 )
#             },
#             {
#                 "text" : "Maybe later..",
#                 "callback" : lambda *args : bot.proceed_next_stage(
#                     STAGE_ENTER_CTF,
#                     STAGE_END,
#                     *args
#                 )
#             }
#         ]
#     )
