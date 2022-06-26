from typing import Optional

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from constants import USERSTATE
from user import User
from stage import Stage


# --------------------------------- FEATURES --------------------------------- #
# - Delete Me
# - Delete Username
# - Delete User
# - Delete All Users
# - Ban User
# - Unban User

# ----------------------------------- USAGE ---------------------------------- #
# Requirements:
# Configure "ADMIN_CHATIDS" in config.yaml to include the chatids for your admins (or just you).

# Example of usage:
# --
# in ../${rootDir}/main.py:

# from bot import Bot
# from stages.admin import AdminConsole

# def main():
#   ...
#
#   bot = Bot()
#   bot.init(BOT_TOKEN, logger)
#
#   STAGE_ADMIN = "admin"
#
#   admin: AdminConsole = AdminConsole(bot)
#   admin.setup(
#     stage_id=STAGE_ADMIN,
#     next_stage_id=NEXT_STAGE,
#     bot=bot
#   )
#
#   ...
#
#   bot.set_first_stage(STAGE_ADMIN)
#   bot.start(live_mode=LIVE_MODE)
# --

# In the example above, we have the AdminConsole stage as the first stage of the bot.
# Any non-admin users will automatically skip this stage and move on to the NEXT_STAGE.
# You can also have the AdminConsole stage be at any point in your bot flow.

# ---------------------------------------------------------------------------- #


class AdminConsole(Stage):
    def __init__(self, stage_id: str, next_stage_id: str, bot):
        return super().__init__(stage_id, next_stage_id, bot)

    def setup(self) -> None:
        self.init_users_data()

        self.states = {
            "MENU": [
                CallbackQueryHandler(
                    self.prompt_delete_me, pattern="^admin_delete_me$"),
                CallbackQueryHandler(
                    self.prompt_delete_user_name, pattern="^admin_delete_user_name$"),
                CallbackQueryHandler(
                    self.prompt_delete_user, pattern="^admin_delete_user$"),
                CallbackQueryHandler(
                    self.prompt_delete_all_users, pattern="^admin_delete_all_users$"),
                CallbackQueryHandler(
                    self.prompt_ban_user, pattern="^admin_ban_user$"),
                CallbackQueryHandler(
                    self.prompt_unban_user, pattern="^admin_unban_user$"),
                CallbackQueryHandler(
                    self.stage_exit, pattern="^admin_exit$"),
            ]
        }
        self.bot.register_stage(self)
        self.MENU = list(self.states.values())[0]

        self.DELETE_USER_NAME_STAGE = self.bot.get_input_from_user(
            input_label="admin_delete_user_name",
            input_text="Enter the User ID to delete username from:",
            input_handler=self.delete_user_name
        )

        self.DELETE_USER_STAGE = self.bot.get_input_from_user(
            input_label="admin_reset_user",
            input_text="Enter the User ID to delete:",
            input_handler=self.reset_user
        )

        self.DELETE_ALL_USERS_STAGE = self.bot.let_user_choose(
            "admin:delete_all_users",
            choice_text="Are you sure you want to delete <b>ALL</b>"
                        " users data?",
            choices=[
                {
                    "text": "Yes",
                    "callback": lambda update, context: self.reset_all_users(update, context)
                },
                {
                    "text": "No",
                    "callback": lambda update, context: self.load_admin(update, context)
                }
            ]
        )

        self.BAN_USER_STAGE = self.bot.get_input_from_user(
            input_label="admin_ban_user",
            input_text="Enter the User ID to ban:",
            input_handler=self.ban_user
        )

        self.UNBAN_USER_STAGE = self.bot.get_input_from_user(
            input_label="admin_unban_user",
            input_text="Enter the User ID to unban:",
            input_handler=self.unban_user
        )

    def init_users_data(self) -> None:
        return super().init_users_data()

    def stage_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")

        if user.chatid in self.bot.admin_chatids:
            user.logger.info("USER_IS_ADMIN_USER",
                             f"User:{user.chatid} is an  admin, loading admin console")
            return self.load_admin(update, context)
        else:
            user.logger.info("USER_IS_NORMAL_USER",
                             f"User:{user.chatid} does not have admin privilege, skipping admin console")
            return self.stage_exit(update, context)

    def stage_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        return super().stage_exit(update, context)

    def load_admin(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        self.bot.edit_or_reply_message(
            update, context,
            f"Welcome to the Admin Console",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "Delete Me", callback_data="admin_delete_me")],
                [InlineKeyboardButton(
                    "Delete User's Username", callback_data="admin_delete_user_name")],
                [InlineKeyboardButton(
                    "Delete User", callback_data="admin_delete_user")],
                [InlineKeyboardButton(
                    "Delete All Users", callback_data="admin_delete_all_users")],
                [InlineKeyboardButton(
                    "Ban User", callback_data="admin_ban_user")],
                [InlineKeyboardButton(
                    "Unban User", callback_data="admin_unban_user")],
                [InlineKeyboardButton(
                    "Back to Bot", callback_data="admin_exit")]
            ])
        )

        return self.MENU

    def prompt_delete_me(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        user.reset_user()

        return self.load_admin(update, context)

    def prompt_delete_user_name(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.DELETE_USER_NAME_STAGE,
            update=update, context=context
        )

    def prompt_delete_user(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.DELETE_USER_STAGE,
            update=update, context=context
        )

    def prompt_delete_all_users(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.DELETE_ALL_USERS_STAGE,
            update=update, context=context
        )

    def prompt_ban_user(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.BAN_USER_STAGE,
            update=update, context=context
        )

    def prompt_unban_user(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.UNBAN_USER_STAGE,
            update=update, context=context
        )

    def delete_user_name(self, chatid: str, update: Update, context: CallbackContext) -> USERSTATE:
        target_user: Optional[User] = self.user_manager.get_from_chatid(chatid)

        if target_user:
            target_user.data.update({"username": ""})
            target_user.save_user_to_file()

        return self.load_admin(update, context)

    def reset_user(self, chatid: str, update: Update, context: CallbackContext) -> USERSTATE:
        target_user: Optional[User] = self.user_manager.get_from_chatid(chatid)

        if target_user:
            target_user.reset_user()

        return self.load_admin(update, context)

    def reset_all_users(self, update: Update, context: CallbackContext) -> USERSTATE:
        for chatid, user in self.user_manager.users.items():
            user: User = user
            user.reset_user()

        return self.load_admin(update, context)

    def ban_user(self, chatid: str, update: Update, context: CallbackContext) -> USERSTATE:
        target_user: Optional[User] = self.user_manager.get_from_chatid(chatid)

        if target_user:
            self.user_manager.ban_user(chatid)

        return self.load_admin(update, context)

    def unban_user(self, chatid: str, update: Update, context: CallbackContext) -> USERSTATE:
        self.user_manager.unban_user(chatid)

        return self.load_admin(update, context)
