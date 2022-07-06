from telegram import Update
from telegram.ext import CallbackContext

from constants import USERSTATE
from stage import Stage


class EchoTen(Stage):

    def __init__(self, stage_id: str, next_stage_id: str, bot):
        super().__init__(stage_id, next_stage_id, bot)

    def setup(self) -> None:
        self.init_users_data()

        self.states = {}

        self.INPUT_ECHO_HANDLER_STAGE: Stage = self.bot.get_user_input(
            stage_id="input_echoten_echo_msg",
            input_text="Please send a message... any message will do:\n\n"
            "Use /cancel to exit.",
            input_handler=self.echo_message,
            exitable=True
        )
        self.bot.register_stage(self)
        # USERSTATES
        # (self.___,) = self.unpacked_states

    def init_users_data(self) -> None:
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.INPUT_ECHO_HANDLER_STAGE.stage_id,
            update=update, context=context
        )

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)

    def echo_message(self, input_message: str, update: Update, context: CallbackContext) -> USERSTATE:
        for _ in range(0, 10):
            self.bot.edit_or_reply_message(
                update=update, context=context,
                text=input_message,
                reply_message=True
            )

        return self.stage_entry(update, context)
