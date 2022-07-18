#!/usr/bin/env python3
import sys
sys.path.append("src")

import logging
import os
import shutil

from typing import Union
from bot import Bot
from user import UserManager
from utils import utils
from utils.log import Log

from stages.admin import AdminConsole
from stages.authenticate import Authenticate
from stages.example_stage import Example

LOG_FILE = os.path.join("logs", f"example_main.log")

CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
assert CONFIG, "Failed to load config.yaml. Fatal error, please remedy."\
    "\n\nLikely an invalid format."

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
    """
    Entry point for the project.

    These classes must always be initialized regardless of stages used:
        1) `Log`

        2) `Bot`, `UserManager`

        Bot and UserManager depends on Log hence the order.


    The chatbot flow is determined by flow of stages below.

        /start -> (`starting-stage`) StageA -> StageB -> StageC -> `EndStage`

    ---

    To set the flow from one stage to another:

        >>> STAGE_SOME_STAGE = "some_stage"
            STAGE_AFTER_SOME_STAGE = "..."
            # ...
            some_stage : SomeStage = SomeStage(
                stage_id=STAGE_SOME_STAGE,
                next_stage_id=STAGE_AFTER_SOME_STAGE,

                bot=bot
            )

        bot is an object of class (:class:`Bot`)

    ---

    To set `starting-stage`:

        >>> STAGE_STARTING_STAGE = "starting_stage"
            STAGE_SECOND_STAGE = "..."
            # ...
            starting_stage : StartingStage = StartingStage(
                stage_id=STAGE_STARTING_STAGE,
                next_stage_id=STAGE_SECOND_STAGE,
                bot=bot
            )
            starting_stage.setup(...)
            bot.set_first_stage(STAGE_STARTING_STAGE)

    ---

    Creating `EndStage`:

        >>> STAGE_END = "end"
            # ...
            bot.make_end_stage(
                stage_id=STAGE_END,
                goodbye_message="You have exited the conversation. Use /start to begin a new one.",
            )

    ---

    To set next_stage of a stage as `EndStage`:

        >>> STAGE_LAST_STAGE = "starting_stage"
            STAGE_END = "end"
            # ...
            last_stage : LastStage = LastStage(
                stage_id=STAGE_LAST_STAGE,
                next_stage_id=STAGE_END,
                bot=bot
            )
            last_stage.setup(...)
            # ...
            bot.make_end_stage(
                stage_id=STAGE_END,
                goodbye_message="You have exited the conversation. Use /start to begin a new one.",
            )

    ---

    To exit conversation from within a stage:

        - Option 1:

            >>> def some_state_in_a_stage(self: Stage, update: Update, context: CallbackContext) -> USERSTATE:
                    query = update.callback_query
                    if query:
                        query.answer()
                    # ...
                    return bot.exit_conversation(
                        current_stage_id=self.stage_id,
                        update=update, context=context
                    )

        - Option 2:

            >>> def some_state_in_a_stage(self: Stage, update: Update, context: CallbackContext) -> USERSTATE:
                    query = update.callback_query
                    if query:
                        query.answer()
                    # ...
                    return bot.proceed_next_stage(
                        current_stage_id=self.stage_id,
                        next_stage_id=bot.end_stage.stage_id,
                        update=update, context=context
                    )
    """

    setup()

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

    STAGE_ADMIN = "admin"
    STAGE_AUTHENTICATE = "authenticate"
    STAGE_COLLECT_USERNAME = "info_collect_username"
    STAGE_COLLECT_EMAIL = "info_collect_email"
    STAGE_EXAMPLE = "example"
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
        if input_str is True:
            return "Only alphanumeric characters"
        else:
            return utils.format_input_str(input_str, True)

    bot.get_user_info(
        stage_id=STAGE_COLLECT_USERNAME,
        next_stage_id=STAGE_COLLECT_EMAIL,
        data_label="username",
        input_formatter=format_name_input,
        additional_text="This is the name displayed on the leaderboard.",
        allow_update=True
    )
    # ---------------------------------------------------------------------------- #

    # ------------------------- Stage: info_collect_email ------------------------ #
    def format_email_input(input_str: Union[str, bool]):
        if input_str is True:
            return "example@domain.com"
        else:
            input_str = utils.format_input_str(input_str, True, "@.")
            return utils.check_if_valid_email_format(input_str)

    bot.get_user_info(
        stage_id=STAGE_COLLECT_EMAIL,
        next_stage_id=STAGE_EXAMPLE,
        data_label="email",
        input_formatter=format_email_input,
        additional_text=None,
        allow_update=True
    )
    # ---------------------------------------------------------------------------- #

    # ------------------------------ Stage: example ------------------------------ #
    example: Example = Example(
        stage_id=STAGE_EXAMPLE,
        next_stage_id=STAGE_END,
        bot=bot
    )
    example.setup()
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
