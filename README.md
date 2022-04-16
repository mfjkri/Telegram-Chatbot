# STATES & STAGES 

Throughout this project, you will see a lot of references about stages and states.\
Below is a brief explanation for them however it does not cover the implementation details behind them.

A `state` is a single situation that the `User` can be in. A User can be in only one given state at any time.

&emsp;Each state will have some amount of `callback handlers`. \
&emsp;There are two types of callback handlers:\
    &emsp;&emsp;1) `CallbackQueryHandler` - called when user presses a given `InlineKeyboardButton` \
    &emsp;&emsp;&emsp;This handler is specific to the button meaning that the `pattern` of the CallbackQueryHandler must match the `callback_data` of the InlineKeyboardButton. \
    \
    &emsp;&emsp;2) `MessageHandler` - called when user sends a message \
    &emsp;&emsp;&emsp;This handler is non-specific and will be called for every message the user sends. Proper steps must be taken to prevent user from submitting data more than once. 
    
A `stage` is a essentially a collection of states with added functionality to allow the creation of complex logic. Stages can also be nested within stages allowing the use of inbuilt stages in your custom stages.

&emsp;Each stage has:\
&emsp;&emsp;1) An `entry` function.  
    &emsp;&emsp;&emsp;This is the function called when loading the stage from another stage in `bot.proceed_next_stage`

&emsp;&emsp;2) An `exit` function.  
    &emsp;&emsp;&emsp;This is an optional callback but good to have if the stage has multiple exit points that leads to the same outcome.

&emsp;&emsp;3) States  
    &emsp;&emsp;&emsp;This is an dictionary of states that the stage can be in.  \
    &emsp;&emsp;&emsp;Each state has callback handlers to handle any action done in that state. \
    \
    &emsp;&emsp;&emsp;{ "STATE_NAME" : [  
    &emsp;&emsp;&emsp;&emsp;CallbackQueryHandler(callback_function, pattern=state_pattern, run_async=True),  
    &emsp;&emsp;&emsp;&emsp;MessageHandler(Filters.all, callback_function, run_async=True)  
    &emsp;&emsp;&emsp;]}

For a more detailed explanation, please refer to the [Implementation Documentation](www.google.com) page.

---

## Inbuilt stages

#### let_user_choose

Presents a variable number of choices to the user. The choices are in the form of buttons (ReplyMarkupButton).

```
def callback(choice_selected : str, update : Update, context : CallbackContext) -> USERSTATE:
    print("Choice selected was:", choice_selected)
    return Bot.proceed_next_stage(
        current_stage_id="choose:example_choice",
        next_stage_id=NEXT_STAGE_ID,
        update=update, context=context
    )
    
example_choose = Bot.let_user_choose(
    choice_label="example_choice",
    choice_text="Please choose from the following:",
    choices = [
        {"text" : "Choice A", "callback" : lambda update, context : callback("A", update, context)},
        {"text" : "Choice B", "callback" : lambda update, context : callback("B", update, context)},
        {"text" : "Choice C", "callback" : lambda update, context : callback("C", update, context)}
    ],
    choices_per_row=2
)

# Proceeding to the stage:
def some_state_or_stage(update : Update, context : CallbackContext) -> USERSTATE:
    query = update.callback_query
    query.answer()
    
    return Bot.proceed_next_stage(
        current_stage_id=CURRENT_SOME_STATE_OR_STAGE_ID,
        next_stage_id=example_choose or "choose:example_choice",
        update=update, context=context
    )                                

# -------------
# A more dynamic choice stage
fruit_choices = ["Apple", "Pear", "Oranges]

choices = []
for fruit in fruit_choices:
    choices.append({
        "text": fruit, "callback" : lambda update, context, fruit=fruit : callback(fruit, update, context)
    })
example_choose = Bot.let_user_choose(
    choice_label="example_choice",
    choice_text="Please choose from the following:",
    choices = choices,
    choices_per_row=2
)
```

#### get_input_from_user

Presents an input field to the user. Input is capture through the next valid message sent from input prompt.

```
def callback(input_given : str, update : Update, context : CallbackContext) -> USERSTATE:
    print("Input given was:", input_given)  
    return Bot.proceed_next_stage(  
        current_stage_id="input:example_input",  
        next_stage_id=NEXT_STAGE_ID,  
        update=update, context=context  
    )  
  
example_input = Bot.get_input_from_user(
    input_label="example_input",
    input_text="Please input your ____:",
    input_handler=callback
)  
  
# Proceeding to the stage:  
def some_state_or_stage(update : Update, context : CallbackContext) -> USERSTATE:  
    query = update.callback_query  
    query.answer()  
  
    return Bot.proceed_next_stage(  
        current_stage_id=CURRENT_SOME_STATE_OR_STAGE_ID,  
        next_stage_id=example_input or "input:example_input",  
        update=update, context=context  
)
```

#### get_info_from_user

Similar to `get_input_from_user` except that the input is a user information and is stored globally in the userdata. No additional logic implementation is required.

```
def format_number_input(input_str : Union[str, bool]):
    if input_str is True:
        return "91234567"
    else:
        if input_str.find("+65") >= 0:
            input_str = input_str[3:]
        input_str = utils.format_input_str(input_str, False, "0123456789")
        return input_str if (
            len(input_str) == 8 and "689".find(input_str[0]) >= 0
        ) else False

example_info = bot.get_info_from_user( # This stage id is collect:phone number
    data_label="phonenumber", 
    next_stage_id=NEXT_STAGE_ID, 
    input_formatter=format_number_input, 
    additional_text="We will not use this to contact you.",
    allow_update=True
)

# Proceeding to the stage: (for get_info_from_user this is usually done at the start of the chatbot flow path)  
def some_state_or_stage(update : Update, context : CallbackContext) -> USERSTATE:  
    query = update.callback_query  
    query.answer()  
  
    return Bot.proceed_next_stage(  
        current_stage_id=CURRENT_SOME_STATE_OR_STAGE_ID,  
        next_stage_id=example_info or "collect:phonenumber",  
        update=update, context=context  
)
```

---

## Creating a custom stage

### Example of a stage: 

src/stages/example.py

```
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from bot import (Bot, USERSTATE)
from user import (User, Users)

class Example(object):
    def __init__(self, bot : Bot):
        self.bot : Bot = bot
        self.users : Users = Users()
        
        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None
        
        self.init_users_data()
        bot.add_custom_stage_handler(self)
        
    def init_users_data(self) -> None:
        self.users.add_data_field("example_state", {
            "score" : 0,
            "gender" : None,
        })
    
    def entry_example(self, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()
            
        return self.load_menu(update, context)
    
    def exit_example(self, update : Update, context : CallbackContext) -> USERSTATE:
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
            entry=self.entry_example,
            exit=self.exit_example,
            states={
                "MENU" : [
                    CallbackQueryHandler(self.prompt_question, pattern="^example_prompt_question$", run_async=True),
                    CallbackQueryHandler(self.prompt_gender_selection, pattern="^example_prompt_gender$", run_async=True),
                ]
            }
        )
        
        self.SELECT_GENDER = self.bot.let_user_choose(
            choice_label="example_sex",
            choice_text="Please select your sex",
            choices=[
              {
                  "text" : "Male",
                  "callback" : lambda update, context : self.gender_selected("Male", update, context)
              },  
              
              {
                  "text" : "Female",
                  "callback" : lambda update, context : self.gender_selected("Female", update, context)
              },

            ],
            choices_per_row=2
        )
        self.QUESTION_STAGE = self.bot.get_input_from_user(
            input_label="example_question",
            input_text="What is 1 + 1?",
            input_handler=self.check_answer
        )

        self.states = self.stage["states"]
        self.MENU = self.bot.unpack_states(self.states)[0]
    
    def load_menu(self, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()
        
        user : User = context.user_data.get("user")
        example_state = user.data.get("example_state")
        
        gender = example_state.get("gender", "undefined")
        score = example_state.get("score")
        
        self.bot.edit_or_reply_message(
            update=update, context=context,
            text=f"Hi!\n\nGender: <b>{gender}</b>\nScore: <b>{score}</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Attempt Question", callback_data="example_prompt_question")],
                [InlineKeyboardButton("Select Gender", callback_data="example_prompt_gender")],
            ])
        )
        return self.MENU
    
    def prompt_question(self, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()
        
        user : User = context.user_data.get("user")
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
        
    def prompt_gender_selection(self, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.SELECT_GENDER,
            update=update, context=context
        )
        
    def check_answer(self, answer : str, update : Update, context : CallbackContext) -> USERSTATE:
        user : User = context.user_data.get("user")
        example_state = user.data.get("example_state")
        
        answer = "".join(char for char in answer if char.isalnum())
        
        if answer == "2":
            example_state["score"]  = 10
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
        
    def gender_selected(self, gender : str, update : Update, context : CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()
        
        user : User = context.user_data.get("user")
        example_state = user.data.get("example_state")
        
        example_state["gender"] = gender
        user.save_user_to_file()
        
        self.bot.edit_or_reply_message(
            update, context,
            text=f"You have selected the option: {gender}!"
        )
        
        return self.load_menu(update, context)
```

### Example of main.py:

src/main.py

```
#!path\to\venv\bin\python.exe
import sys, logging, os
from typing import (Union)

from bot import Bot
from user import Users
import utils.utils as utils
from utils.log import Log 
from stages.example import Example

LOG_FILE = os.path.join("logs", f"csabot.log")
CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
BOT_TOKEN = CONFIG["BOT_TOKENS"]["LIVE"]

def main(): 
    logger = Log(
        name=__name__,
        stream_handle=sys.stdout,
        file_handle=LOG_FILE,
        log_level= logging.DEBUG
    )
    
    users = Users()    
    users.init(logger)
    
    bot = Bot()
    bot.init(BOT_TOKEN, logger)

    STAGE_COLLECT_NAME = "collect:name"
    STAGE_COLLECT_EMAIL = "collect:email"
    STAGE_EXAMPLE = "example"
    STAGE_END = "end"


    # Stage collect:name
    def format_name_input(input_str : Union[str, bool]):
        if input_str is not True:
            return utils.format_input_str(input_str, True, "' ")
    bot.get_info_from_user( # This stage id is collect:name
        data_label="name",
        next_stage_id=STAGE_COLLECT_EMAIL,
        input_formatter=format_name_input,
        allow_update=True
    )

    # Stage collect:email
    def format_email_input(input_str : Union[str, bool]):
        if input_str is True:
            return "example@domain.com"
        else:
            input_str = utils.format_input_str(input_str, True, "@.")
            return utils.check_if_valid_email_format(input_str)            
    bot.get_info_from_user( # This stage id is collect:email
        data_label="email", 
        next_stage_id=STAGE_EXAMPLE, 
        input_formatter=format_email_input, 
        additional_text=None, #"⚠ This will be the only channel that we use to contact or share opportunities via.",
        allow_update=True
    )
        
    # Stage Example
    example : Example = Example(bot)
    example.setup(
        stage_id=STAGE_EXAMPLE,
        next_stage_id=STAGE_END
    )
    
    # Start Bot
    logger.info(False, "")
    logger.info(False, "Initializing...")
    logger.info(False, "")
    bot.set_first_stage(STAGE_COLLECT_NAME)
    bot.start()


if __name__ == "__main__":
    main()
```

<hr>

# TECHNICAL DOCUMENTATION

