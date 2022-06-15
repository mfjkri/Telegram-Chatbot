from typing import List

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from bot import (MESSAGE_DIVIDER, Bot, USERSTATE)
from user import (UserManager, User)
import utils.utils as utils


# --------------------------------- FEATURES --------------------------------- #
# - Only allow authorized users to use Bot
# - Categorize users based on user groups

# ----------------------------------- USAGE ---------------------------------- #
# Requirements:
# Configure "PASSCODES" in config.yaml to have passcodes passcode:[name, [user-group]]

# Example of usage:
# --
# in ../${rootDir}/main.py:

# from bot import Bot
# from stages.authenticate import Authenticate

# def main():
#   ...
#
#   bot = Bot()
#   bot.init(BOT_TOKEN, logger)
#
#   STAGE_AUTHENTICATE = "authenticate"
#
#   authenticate: Authenticate = Authenticate(bot)
#   authenticate.setup(
#       stage_id=STAGE_AUTHENTICATE,
#       next_stage_id=NEXT_STAGE
#   )
#
#   ...
#
#   bot.set_first_stage(STAGE_AUTHENTICATE)
#   bot.start(live_mode=LIVE_MODE)
# --

# In the example above, we have the Authenticate stage as the first stage of the bot.
# The user will have to verify their indentity with a passcode before being able to use the rest of the bot.
# You can also have the Authenticate stage be at any point in your bot flow.
#   For example, if you have AdminConsole enabled and set as the first stage,
#   Have the next stage_id of AdminConsole be set to STAGE_AUTHENTICATE

# ---------------------------------------------------------------------------- #


class Authenticate(object):
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
        self.user_manager.add_data_field("name", "")
        self.user_manager.add_data_field("group", "")

    def entry_authenticate(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")

        if user.data.get("name"):
            return self.exit_authenticate(update, context)
        else:
            return self.bot.proceed_next_stage(
                current_stage_id=self.stage_id,
                next_stage_id=self.PROMPT_AUTHENTICATION,
                update=update, context=context
            )

    def exit_authenticate(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query and query:
            query.answer()

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
            entry=self.entry_authenticate,
            exit=self.exit_authenticate,
            states={
                "IDENTITY_CONFIRMATION": [
                    CallbackQueryHandler(
                        self.confirm_choice, pattern=f"^auth_accept_identity$", run_async=True),
                    CallbackQueryHandler(
                        self.decline_identity, pattern=f"^auth_decline_identity$", run_async=True)
                ],
                "CONFIRM_CHOICE": [
                    CallbackQueryHandler(
                        self.accept_identity, pattern=f"^auth_confirm_choice$", run_async=True),
                    CallbackQueryHandler(
                        self.decline_identity, pattern=f"^auth_cancel_choice$", run_async=True)
                ]
            }
        )

        self.PROMPT_AUTHENTICATION = self.bot.get_input_from_user(
            input_label="authenticate:passcode",
            input_text="Please enter your passcode:",
            input_handler=self.check_passcode,
            exitable=True
        )

        self.states = self.stage["states"]
        self.IDENTITY_CONFIRMATION, self.CONFIRM_CHOICE = self.bot.unpack_states(
            self.states)

    def check_passcode(self, input_passcode: str, update: Update, context: CallbackContext) -> USERSTATE:

        user: User = context.user_data.get("user")
        sanitized_input = utils.format_input_str(
            input_passcode, alphanumeric=True)

        passcodes = self.bot.user_passcodes
        if sanitized_input in passcodes:
            user.logger.info(f"USER_AUTHENTICATE_CORRECT_PASSCODE",
                             f"User:{user.chatid} has entered a valid passcode")

            lookup, is_lookup_an_array = passcodes[sanitized_input], isinstance(
                passcodes[sanitized_input], List)
            name = lookup[0] if is_lookup_an_array else lookup
            group = lookup[1] if is_lookup_an_array else "none"

            # This check is actually redundant since we already bypassed authenticated for users with a valid name field.
            if user.data.get("name") == name:
                return self.exit_authenticate(update, context)
            else:
                return self.confirm_identify(
                    name, group,
                    update, context
                )
        else:
            user.logger.info(f"USER_AUTHENTICATE_WRONG_PASSCODE",
                             f"User:{user.chatid} has tried an invalid passcode: @{sanitized_input}@")

            self.bot.edit_or_reply_message(
                update, context,
                "You have entered a wrong passcode. Please try again."
            )
            return self.bot.proceed_next_stage(
                current_stage_id=self.stage_id,
                next_stage_id=self.PROMPT_AUTHENTICATION,
                update=update, context=context
            )

    def confirm_identify(self, name: str, group: str, update: Update, context: CallbackContext) -> USERSTATE:
        context.user_data.update({"pending_name": name})
        context.user_data.update({"pending_group": group})

        confirmation_text = f"Please confirm your identity.\n\n"
        confirmation_text += MESSAGE_DIVIDER
        confirmation_text += f"<b>{name}</b>\n"
        confirmation_text += MESSAGE_DIVIDER

        self.bot.edit_or_reply_message(
            update, context,
            text=confirmation_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Yes that's me", callback_data="auth_accept_identity"),
                    InlineKeyboardButton(
                        "❌", callback_data="auth_decline_identity")
                ]
            ])
        )

        return self.IDENTITY_CONFIRMATION

    def accept_identity(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        pending_name = context.user_data.pop("pending_name")

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_AUTHENTICATE_ACCEPT_IDENTITY",
                         f"User:{user.chatid} has accepted the identity: @{pending_name}@")

        user.update_user_data(
            "name",
            pending_name
        )
        user.update_user_data(
            "username",
            pending_name
        )
        user.update_user_data(
            "group",
            context.user_data.pop("pending_group")
        )

        return self.exit_authenticate(update, context)

    def decline_identity(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        pending_name = context.user_data.pop("pending_name")
        context.user_data.pop("pending_group")

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_AUTHENTICATE_DECLINE_IDENTITY",
                         f"User:{user.chatid} has declined the identity: @{pending_name}@")

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.PROMPT_AUTHENTICATION,
            update=update, context=context
        )

    def confirm_choice(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_AUTHENTICATE_CONFIRM_IDENTITY",
                         f"User:{user.chatid} has confirmed the accepted identity")

        self.bot.edit_or_reply_message(
            update, context,
            text="Are you sure?\n\n<i>This action is nonreversible.</i>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Yes", callback_data="auth_confirm_choice"),
                    InlineKeyboardButton(
                        "❌", callback_data="auth_cancel_choice")
                ]
            ])
        )

        return self.CONFIRM_CHOICE
