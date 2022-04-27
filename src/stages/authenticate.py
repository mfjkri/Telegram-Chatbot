from typing import (Union)

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from user import Users, User
from bot import (Bot, USERSTATE)
import utils.utils as utils

PASSCODES = {
    # START_OF_PASSCODES_MARKER
    "A123" : "Johnny",
    # END_OF_PASSCODES_MARKER
}


class Authenticate(object):
    def __init__(self, bot : Bot):
        self.bot : Bot = bot
        self.users : Users = Users()
        
        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None
        
        bot.add_custom_stage_handler(self)
        self.init_users_data()
        
        
    def init_users_data(self) -> None:
        self.users.add_data_field("name", None)
    
    
    def entry_authenticate(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()
        
        user : User = context.user_data.get("user")
        
        if user.data.get("name") is not None:
            return self.exit_authenticate(update, context) 
        else:
            return self.bot.proceed_next_stage(
                current_stage_id=self.stage_id,
                next_stage_id=self.PROMPT_AUTHENTICATION,
                update=update, context=context
            )
    
    
    def exit_authenticate(self, update: Update, context: CallbackContext) -> USERSTATE:
        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.next_stage_id,
            update=update, context=context
        )
    
    
    def setup(self, stage_id : str, next_stage_id : str) -> None:
        self.stage_id = stage_id
        self.next_stage_id = next_stage_id
        
        self.stage = self.bot.add_stage(
            stage_id=stage_id,
            entry=self.entry_authenticate,
            exit=self.exit_authenticate,
            states={
                # TODO : Add States and stages for verification process
                "CONFIRMATION_CHOICE" : [
                    CallbackQueryHandler(self.accept_identity, pattern=f"^auth_accept_identity$", run_async=True),
                    CallbackQueryHandler(self.decline_identity, pattern=f"^auth_decline_identity$", run_async=True)
                ]
            }
        )
        
        self.PROMPT_AUTHENTICATION = self.bot.get_input_from_user(
            input_label="authenticate:passcode",
            input_text="Please enter your passcode:",
            input_handler=self.check_passcode
        )
        
        self.states = self.stage["states"]
        self.CONFIRMATION_CHOICE = self.bot.unpack_states(self.states)[0]


    def check_passcode(self, input_passcode : str, update : Update, context : CallbackContext) -> USERSTATE:
        
        user : User = context.user_data.get("user")
        sanitized_input = utils.format_input_str(input_passcode, alphanumeric=True)
        
        if sanitized_input in PASSCODES:
            # This check is actually redundant since we already bypassed authenticated for users with a valid name field.
            if user.data.get("name") == PASSCODES[sanitized_input]:
                return self.exit_authenticate(update, context) 
            else:
                return self.confirm_identify(
                    PASSCODES[sanitized_input],
                    update, context
                )
        else:    
            self.bot.edit_or_reply_message(
                update, context,
                "You have entered a wrong passcode. Please try again."
            )
            return self.bot.proceed_next_stage(
                current_stage_id=self.stage_id,
                next_stage_id=self.PROMPT_AUTHENTICATION,
                update=update, context=context
            )
        
        
        
    def confirm_identify(self, name : str, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()
            
        context.user_data.update({"pending_name" : name})
        
        self.bot.edit_or_reply_message(
            update, context,
            f"Please confirm your identity.\n\n Are you <b>{name}</b>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Yes", callback_data="auth_accept_identity"),
                    InlineKeyboardButton("No", callback_data="auth_decline_identity")
                ]
            ]) 
        )
        
        return self.CONFIRMATION_CHOICE
    
    def accept_identity(self, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()
            
        user : User = context.user_data.get("user")
        pending_name = context.user_data.get("pending_name")
        
        user.update_user_data("name", pending_name)
        context.user_data.pop("pending_name")
        return self.exit_authenticate(update, context) 
    
    def decline_identity(self, update : Update, context :CallbackContext) -> USERSTATE:
        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.PROMPT_AUTHENTICATION,
            update=update, context=context
        )