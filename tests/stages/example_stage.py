from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from bot import (Bot, USERSTATE)
from user import (User, UserManager)


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
#
#   example: Example = Example(bot)
#   example.setup(
#       stage_id=STAGE_EXAMPLE,
#       next_stage_id=NEXT_STAGE
#   )
#
#   ...
#
#   bot.set_first_stage(STAGE_EXAMPLE)
#   bot.start(live_mode=LIVE_MODE)
# --

# ---------------------------------------------------------------------------- #


class Example(object):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.user_manager: UserManager = UserManager()

        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None

        bot.add_custom_stage_handler(self)
        self.init_users_data()

    def init_users_data(self) -> None:
        self.user_manager.add_data_field("example_state", {
            "score": 0,
            "color": None,
        })

    def entry_example(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        return self.load_menu(update, context)

    def exit_example(self, update: Update, context: CallbackContext) -> USERSTATE:
        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.next_stage_id,
            update=update, context=context
        )

    def setup(self, stage_id: str, next_stage_id: str) -> None:
        self.stage_id = stage_id
        self.next_stage_id = next_stage_id

        self.stage = self.bot.add_stage(
            stage_id=stage_id,
            entry=self.entry_example,
            exit=self.exit_example,
            states={
                "MENU": [
                    CallbackQueryHandler(
                        self.prompt_question, pattern="^example_prompt_question$", run_async=True),
                    CallbackQueryHandler(
                        self.prompt_color_selection, pattern="^example_prompt_color$", run_async=True),
                    CallbackQueryHandler(
                        self.exit_example, pattern="^example_exit$", run_async=True),
                ]
            }
        )
        self.states = self.stage["states"]

        self.SELECT_COLOR = self.bot.let_user_choose(
            choice_label="example_color",
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
        self.QUESTION_STAGE = self.bot.get_input_from_user(
            input_label="example_question",
            input_text="What is 1 + 1?",
            input_handler=self.check_answer
        )
        self.MENU = self.bot.unpack_states(self.states)[0]

    def load_menu(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        color = example_state.get("color", "undefined")
        score = example_state.get("score")

        self.bot.edit_or_reply_message(
            update=update, context=context,
            text=f"Hi!\n\nColor: <b>{color}</b>\nScore: <b>{score}</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "Attempt Question", callback_data="example_prompt_question")],
                [InlineKeyboardButton(
                    "Select Color", callback_data="example_prompt_color")],
                [InlineKeyboardButton(
                    "Exit Example 👋", callback_data="example_exit")]
            ]),
            reply_message=True
        )
        return self.MENU

    def prompt_question(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        if example_state["score"] == 0:
            return self.bot.proceed_next_stage(
                current_stage_id=self.stage_id,
                next_stage_id=self.QUESTION_STAGE,
                update=update, context=context
            )
        else:
            self.bot.edit_or_reply_message(
                update, context,
                text=f"You have already completed this question!"
            )
            return self.load_menu(update, context)

    def prompt_color_selection(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.SELECT_COLOR,
            update=update, context=context
        )

    def check_answer(self, answer: str, update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        answer = "".join(char for char in answer if char.isalnum())

        if answer == "2":
            example_state["score"] = 10
            user.save_user_to_file()

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
        user.save_user_to_file()

        self.bot.edit_or_reply_message(
            update, context,
            text=f"You have selected the option: {color}!"
        )

        return self.load_menu(update, context)
