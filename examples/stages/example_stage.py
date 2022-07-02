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
        self.QUESTION_STAGE = self.bot.get_user_input(
            input_label="example_question",
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
        """
        This is the function called when another stage/state is proceeding to it:

            in some other stage or state

            return self.bot.proceed_next_stage(
                current_stage_id = some_other_stage_id,
                next_stage_id = THIS_STAGE_ID,
                update = update, context = context
            )


        The two parameters @update and @context is always assured to exist.
        update will contain information about the trigger leading to this stage
        context will be a "shared" dict passed between all callbacks
            you can find the user class in this

                user: User = context.user_data.get("user")


        For safety, always check in the entry function whether the previous action
        was an InlineKeyboardButton which will have a CallbackQuery that needs to be answered
        Hence this few lines of code should always be at the top of your stages entry function:

            query = update.callback_query
            if query:
                query.answer()


        Normally what hapens after depends on your stage but the most common example,
        is to just call some loader function to display your stage menu.

            return self.load_menu(update, context)
        """

        query = update.callback_query
        if query:
            query.answer()

        return self.load_menu(update, context)

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        """
        This is a function called internally (within this stage).
        It will never be called from outside this stage by default.

        This function is not required but is recommended to be used.
        This ensures that your stage only has only "exit".

        However if your stage design does require there to be multiple exits,
        then you can handle it accordingly and leave this function like this.

        Exiting the stage from within it:

            in some callback function:

            def process_user_input(self, update : Update, context : CallbackContext) -> USERSTATE:
                query = update.callback_query
                query.answer()

                # --- 

                return self.exit_example(update,context)
        """

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
            next_stage_id=self.QUESTION_STAGE,
            update=update, context=context
        )

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

        return self.load_menu(update, context)
