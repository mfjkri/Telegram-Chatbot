from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from bot import (Bot, USERSTATE)
from user import (User, Users)


class Example(object):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.users: Users = Users()

        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None

        self.init_users_data()
        bot.add_custom_stage_handler(self)

    def init_users_data(self) -> None:
        self.users.add_data_field("example_state", {
            "score": 0,
            "gender": None,
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
                        self.prompt_gender_selection, pattern="^example_prompt_gender$", run_async=True),
                ]
            }
        )
        self.states = self.stage["states"]

        self.SELECT_GENDER = self.bot.let_user_choose(
            choice_label="example_sex",
            choice_text="Please select your sex",
            choices=[
                {
                    "text": "Male",
                    "callback": lambda update, context: self.gender_selected("Male", update, context)
                },

                {
                    "text": "Female",
                    "callback": lambda update, context: self.gender_selected("Female", update, context)
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

        gender = example_state.get("gender", "undefined")
        score = example_state.get("score")

        self.bot.edit_or_reply_message(
            update=update, context=context,
            text=f"Hi!\n\nGender: <b>{gender}</b>\nScore: <b>{score}</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "Attempt Question", callback_data="example_prompt_question")],
                [InlineKeyboardButton(
                    "Select Gender", callback_data="example_prompt_gender")],
            ])
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

    def prompt_gender_selection(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.SELECT_GENDER,
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

    def gender_selected(self, gender: str, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        example_state = user.data.get("example_state")

        example_state["gender"] = gender
        user.save_user_to_file()

        self.bot.edit_or_reply_message(
            update, context,
            text=f"You have selected the option: {gender}!"
        )

        return self.load_menu(update, context)
