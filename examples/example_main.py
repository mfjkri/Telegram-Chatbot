# shebang
import sys
sys.path.append("src")

# Our custom stage is at ${rootDir}/examples/stages/example_stage.py
# To be able to import it, we must append dir:${rootDir}/examples/ to path
# For an actual main.py at ${rootDir}/main.py, there is no need to do this
sys.path.append("examples")
from stages.example_stage import Example

import logging
import os
import shutil

from typing import Union
from bot import Bot
from user import UserManager, User
import utils.utils as utils
from utils.log import Log

from stages.admin import AdminConsole
from stages.authenticate import Authenticate

LOG_FILE = os.path.join("logs", f"csabot.log")

CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
LIVE_MODE = CONFIG["RUNTIME"]["LIVE_MODE"]
FRESH_START = CONFIG["RUNTIME"]["FRESH_START"] if not LIVE_MODE else False
BOT_TOKEN = CONFIG["BOT_TOKENS"]["LIVE"] if LIVE_MODE else CONFIG["BOT_TOKENS"]["TEST"]


def setup():
    utils.get_dir_or_create(os.path.join("logs"))
    if FRESH_START:
        users_directory = os.path.join("users")

        for chatid in os.listdir(users_directory):
            user_directory = os.path.join(users_directory, chatid)
            if os.path.isdir(user_directory):
                shutil.rmtree(user_directory)

        if os.path.isfile(LOG_FILE):
            os.remove(LOG_FILE)


def main():
    setup()

    logger = Log(
        name=__name__,
        stream_handle=sys.stdout,
        file_handle=LOG_FILE,
        log_level=logging.DEBUG
    )

    users = UserManager()
    users.init(logger)

    bot = Bot()
    bot.init(BOT_TOKEN, logger)

    STAGE_ADMIN = "admin"
    STAGE_AUTHENTICATE = "authenticate"
    STAGE_COLLECT_USERNAME = "collect:username"
    STAGE_COLLECT_EMAIL = "collect:email"
    STAGE_EXAMPLE = "example"
    STAGE_END = "end"

    # Stage admin
    admin: AdminConsole = AdminConsole(bot)
    admin.setup(
        stage_id=STAGE_ADMIN,           # This stage id is admin
        next_stage_id=STAGE_AUTHENTICATE
    )

    # Stage authenticate
    authenticate: Authenticate = Authenticate(bot)
    authenticate.setup(
        stage_id=STAGE_AUTHENTICATE,    # This stage is authenticate
        next_stage_id=STAGE_COLLECT_USERNAME
    )

    # Stage collect:username
    def format_name_input(input_str: Union[str, bool]):
        if input_str is not True:
            return utils.format_input_str(input_str, True, "' ")
    bot.get_info_from_user(
        data_label="username",          # This stage id is collect:username
        next_stage_id=STAGE_COLLECT_EMAIL,
        input_formatter=format_name_input,
        additional_text="This is the name displayed on the leaderboard.",
        allow_update=True
    )

    # Stage collect:email
    def format_email_input(input_str: Union[str, bool]):
        if input_str is True:
            return "example@domain.com"
        else:
            input_str = utils.format_input_str(input_str, True, "@.")
            return utils.check_if_valid_email_format(input_str)
    bot.get_info_from_user(
        data_label="email",             # This stage id is collect:email
        next_stage_id=STAGE_EXAMPLE,
        input_formatter=format_email_input,
        additional_text=None,
        allow_update=True
    )

    # Stage example
    example: Example = Example(bot)
    example.setup(
        stage_id=STAGE_EXAMPLE,         # This stage id is example
        next_stage_id=STAGE_END
    )

    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")

    bot.set_first_stage(STAGE_ADMIN)
    bot.set_end_of_chatbot(
        lambda update, context: bot.edit_or_reply_message(
            update, context, "You have exited the conversation. \n\nUse /start to begin a new one.")
    )
    bot.start(live_mode=LIVE_MODE)


if __name__ == "__main__":
    main()
