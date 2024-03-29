from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from bot import USERSTATE
from user import User
from stage import Stage


# -------------------------------- TAKE NOTES -------------------------------- #
# In a real stage, you would have its filepath be:
#    ${rootDir}/src/stages/

# and in your main.py:
#   import sys
#   sys.path.append("src")
#
#   from stages.stage_name import stage_class_name

# !!!!!!!!!!
# FOR THE REST OF THIS DOCUMENTATION, IT IS ASSUMED
# THAT YOU HAVE THIS STAGE, PARENTED AT,
# ${rootDir}/src/stages/ folder.
# !!!!!!!!!!

# --------------------------------- FEATURES --------------------------------- #
# - Single-questionaire (Attempt Question)
# - Single two options choice (Select Color)

# ----------------------------------- USAGE ---------------------------------- #
# Requirements:
# -

# Example of usage:
# --
# in ../${rootDir}/main.py:

# from bot import Bot
# from stages.example_stage import Example

# def main():
#   ...
#
#   bot = Bot()
#   bot.init(BOT_TOKEN, logger)
#
#   STAGE_EXAMPLE = "example"
#   ...
#
#   # ------------------------------ Stage: example ------------------------------ #
#   example: Example = Example(
#       stage_id=STAGE_EXAMPLE,
#       next_stage_id=NEXT_STAGE,
#       bot=bot
#   )
#   example.setup()
#   bot.set_first_stage(STAGE_EXAMPLE)
#   # ---------------------------------------------------------------------------- #
#
#   ...
#
#   bot.start(live_mode=LIVE_MODE)
# --

# ---------------------------------------------------------------------------- #


class Example(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        super().__init__(stage_id, next_stage_id, bot)

    def setup(self) -> None:
        self.init_users_data()

        self.states = {
            "MENU": [
                CallbackQueryHandler(
                    self.prompt_question, pattern="^example_prompt_question$"),
                CallbackQueryHandler(
                    self.prompt_color_selection, pattern="^example_prompt_color$"),
                CallbackQueryHandler(
                    self.stage_exit, pattern="^example_exit$"),
            ]
        }
        self.bot.register_stage(self)
        # USERSTATES
        (self.MENU,) = self.unpacked_states

        self.CHOOSE_COLOR_STAGE: Stage = self.bot.let_user_choose(
            stage_id="choose_example_color",
            choice_text="Please select your color",
            choices=[
                {
                    "text": "Red",
                    "callback": lambda update, context: self.color_selected("Red", update, context)
                },

                {
                    "text": "Blue",
                    "callback": lambda update, context: self.color_selected("Blue", update, context)
                },

            ],
            choices_per_row=2
        )
        self.INPUT_QUESTION_STAGE: Stage = self.bot.get_user_input(
            stage_id="input_example_question",
            input_text="What is 1 + 1?",
            input_handler=self.check_answer
        )

    def init_users_data(self) -> None:
        """
        Appends any userdata used by this stage into the main userdata dict
        using the UserManager which will handle all the initializing and actual loading/saving.

        The data label and init value is passed.

        The general guideline for stages is to bundle all its relevant data into
        a "state" dict like below and set an init value for each key entry as well.

        This is to prevent naming conflicts for the data label with other stages.
        """

        self.user_manager.add_data_field("example_state", {
            "score": 0,
            "color": None,
        })
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        return self.load_menu(update, context)

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)

    def load_menu(self, update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        color: str = example_state.get("color", "undefined")
        score: int = example_state.get("score", 0)

        keyboard = [
            [InlineKeyboardButton(
                "Select Color", callback_data="example_prompt_color")],
            [InlineKeyboardButton(
                "Exit Example 👋", callback_data="example_exit")]
        ]

        if score == 0:
            keyboard.insert(
                0,
                [InlineKeyboardButton(
                    "Attempt Question",
                    callback_data="example_prompt_question"
                )],
            )

        self.bot.edit_or_reply_message(
            update=update, context=context,
            text=f"Hi!\n\nScore: <b>{score}</b>\nColor: <b>{color}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return self.MENU

    def prompt_question(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.INPUT_QUESTION_STAGE.stage_id,
            update=update, context=context
        )

    def prompt_color_selection(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.CHOOSE_COLOR_STAGE.stage_id,
            update=update, context=context
        )

    def check_answer(self, answer: str, update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        answer = "".join(char for char in answer if char.isalnum())

        if answer == "2":
            example_state["score"] = 10
            user.save_to_file()

            self.bot.edit_or_reply_message(
                update, context,
                text=f"Your answer: {answer} is correct! You have been awarded 10 points!"
            )
        else:
            self.bot.edit_or_reply_message(
                update, context,
                text=f"Your answer: {answer} is wrong!"
            )
        return self.load_menu(update, context)

    def color_selected(self, color: str, update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        example_state["color"] = color
        user.save_to_file()

        return self.load_menu(update, context)
