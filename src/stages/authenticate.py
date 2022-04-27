from curses.panel import update_panels
from typing import (Union)

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from user import Users, User
from bot import (Bot, USERSTATE)

AUTHORIZED_USERS = [] #"1026217187"

class Authenticate(object):
    def __init__(self, bot : Bot):
        self.bot : Bot = bot
        self.users : Users = Users()
        
        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None
        
        bot.add_custom_stage_handler(self)
        
    
    def entry_authenticate(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()
        
        user : User = context.user_data.get("user")
        # TODO : Prompt verfication
        
        return self.exit_authenticate(update, context)
    
    
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
            }
        )
        
        self.states = self.stage["states"]

