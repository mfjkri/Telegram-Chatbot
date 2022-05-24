# Table of contents

1. [Quickstart](#1-quickstart-reference)
   - [1.1 Setting up](#11-setting-up):
     - [**setup.py**](#111-setuppy)
     - [Building manually](#112-building-manually)
   - [1.2 Configuring **config.yaml**](#12-configuring-configyaml)
   - [1.2 Adding CTF Challenges](#13-adding-ctf-challenges)
   - [1.3 Running Chatbot](#14-running-the-chatbot)
   - [1.3 Using runtime helper_scripts](#)
2. [States & Stages](#2-states--stages)
   - [2.1 Inbuilt stages](#21-inbuilt-stages):
     - [let_user_choose](#211-letuserchoose)
     - [get_input_from_user](#212-getinputfromuser)
     - [get_info_from_user](#213-getinfofromuser)
   - [2.2 Custom stages](#22-creating-a-custom-stage)

&nbsp;

# 1) QUICKSTART REFERENCE

## 1.1) Setting up

&nbsp;

### 1.1.1) `setup.py`:

If you are running **Windows** or **Linux**, you can set up the project and install dependencies using `setup.py`:

```bash
$ cd ${rootDir}
# Replace the "python" argument with whatever your python keyword is
# For example,if your system uses python3:
#       python3 setup.py --setup "python3"

# Linux:
$ python setup.py --setup "python"
# Windows:
$ python .\setup.py --setup "python"
```

Assuming you encounter no errors, you should see something like this:

```bash
2022-05-16 09:51:06,205 [INFO] Changing working directory to: /media/Programming/repos/js/Telegram-Chatbot
2022-05-16 09:51:06,206 [INFO] Creating logs and archives directory...
2022-05-16 09:51:06,206 [INFO] Directory: exports not found. Creating one...
2022-05-16 09:51:06,206 [INFO] Directory: logs not found. Creating one...
2022-05-16 09:51:06,210 [INFO] PYTHON VERSION BEING USED IS: b'Python 3.10.4\n'
2022-05-16 09:51:06,210 [INFO] Creating python venv (if already exists, nothing happens)...
2022-05-16 09:51:16,866 [INFO] No config.yaml file found! Creating one with default template...
2022-05-16 09:51:16,867 [INFO] Setting shebang of main.py to venv intepreter...
2022-05-16 09:51:16,867 [INFO] Setting main.py to be an executable...
...
...
Using legacy 'setup.py install' for tornado, since package 'wheel' is not installed.
Installing collected packages: pytz, certifi, urllib3, tzdata, tornado, six, pyyaml, idna, charset-normalizer, cachetools, requests, pytz-deprecation-shim, tzlocal, APScheduler, python-telegram-bot
  Running setup.py install for tornado ... done
Successfully installed APScheduler-3.6.3 cachetools-4.2.2 certifi-2021.10.8 charset-normalizer-2.0.12 idna-3.3 python-telegram-bot-13.11 pytz-2022.1 pytz-deprecation-shim-0.1.0.post0 pyyaml-6.0 requests-2.27.1 six-1.16.0 tornado-6.1 tzdata-2022.1 tzlocal-4.2 urllib3-1.26.9
WARNING: You are using pip version 22.0.4; however, version 22.1 is available.
```

If setup fails, please refer to [1.1.2) Building manually](#112-building-manually) and follow the steps for where the setup failed.

&nbsp;

### 1.1.2) Building manually:

If you are running any other OS such as **MacOS**, you will have to build the project manually.

1. Go to your project root directory:
   ```bash
   cd ../project_name/
   ```
2. Create the following directories in your root directory:
   - ctf/challenges/
   - exports/
   - logs/
3. Create python `venv`:
   ```bash
   $ python -m venv venv # Or its equivalent on your OS
   ```
4. Install project dependencies into venv:
   ```bash
   $ venv/bin/python -m pip install -r requirements.txt # Or equivalent on your OS
   ```
5. Create `config.yaml`:

   ```yaml
   # ---------------------------------- RUNTIME --------------------------------- #
   RUNTIME:
     LIVE_MODE: false
     FRESH_START: true

   # -------------------------------- BOT TOKENS -------------------------------- #
   BOT_TOKENS:
     LIVE: BOT_TOKEN
     TEST: BOT_TOKEN

   # ------------------------------ USER PASSCODES ------------------------------ #
   USER_PASSCODES:
     {}
     # START_OF_PASSCODES_MARKER
     # END_OF_PASSCODES_MARKER

   # ------------------------------- ADMIN CHATIDS ------------------------------ #
   ADMIN_CHATIDS: []

   # -------------------------------- LOG CONFIG -------------------------------- #
   LOG_USER_TO_APP_LOGS: false
   ```

&nbsp;

---

&nbsp;

## 1.2) Configuring config.yaml

For this program to run correctly, the `config.yaml` file has to be first configured.

```yaml
# ../${rootDir}/config.yaml

# ---------------------------------- RUNTIME --------------------------------- #
RUNTIME:
  LIVE_MODE: false
  FRESH_START: true

# -------------------------------- BOT TOKENS -------------------------------- #
BOT_TOKENS:
  LIVE: BOT_TOKEN
  TEST: BOT_TOKEN

# ------------------------------ USER PASSCODES ------------------------------ #
USER_PASSCODES:
  # START_OF_PASSCODES_MARKER
  A1234: John Smith
  # END_OF_PASSCODES_MARKER

# ------------------------------- ADMIN CHATIDS ------------------------------ #
ADMIN_CHATIDS: []

# -------------------------------- LOG CONFIG -------------------------------- #
LOG_USER_TO_APP_LOGS: false
```

### config.yaml fields reference:

- **`RUNTIME`**:

  If **RUNTIME:LIVE_MODE** is set to `true` then the bot will use **BOT_TOKENS:LIVE** else it will use **BOT_TOKENS:TEST**.

  If **RUNTIME:FRESH_START** is set to `true` then the bot will clear previous log and user files every time it is restarted.\
   For safety purposes, **RUNTIME:FRESH_START** will be **ignored** if **RUNTIME:LIVE_MODE** is `true`.

- **`BOT_TOKENS`**:

  **BOT_TOKENS:LIVE** is the token to connect to the Telegram Bot used for release day.\
  **BOT_TOKENS:TEST** is the token to connect to the Telegram Bot used during development.

- **`USER_PASSCODES`**:

  Each _PASSCODE_ is an entry:

  ```yaml
  PASSCODE:
    - USER NAME
    - USER GROUP
  ```

  _USER GROUP_ can be omitted and will default to "none":

  ```yaml
  PASSCODE: USER NAME
  ```

  Here is an example with more passcodes:

  ```yaml
  # ------------------------------ USER PASSCODES ------------------------------ #
  USER_PASSCODES:
    # START_OF_PASSCODES_MARKER

    #------
    # Generated at 16/05/2022 13:09:13
    # Refer to src/helper_scripts/generate_passcodes.py for more details.

    T3026: Sonya Anhak # Here we can omit User Group entirely
                    # It will be defaulted to none

    T3026:
    - Derek Eng
    - none # We can also explicitly define User Group to be none

    X4853:
    - Rock Lee
    - member

    E9468:
    - Samantha Tan
    - guest

    E4739:
    - John Smith
    - guest

    #------

    # END_OF_PASSCODES_MARKER
  ```

- **`ADMIN_CHATIDS`**:

  Every user with their chatid here will have access to the Admin Console when using the bot assuming that the Admin stage is in use (look through [admin.py](src/stages/admin.py) for more details).

  To obtain your own chatid, you can run the bot in development mode, and use the bot alone. This ensures the only one user created is yours. Alternatively, you can also follow this [guide](https://www.alphr.com/find-chat-id-telegram/).

  Each _CHATID_ is an entry:

  ```yaml
  ADMIN_CHATIDS:
    - 102391029
  ```

  Here is an example with more chatids:

  ```yaml
  ADMIN_CHATIDS:
    - 1203910239
    - 12032190391
    - 40329103192
  ```

  If you do not wish to have any admin chatids:

  ```yaml
  ADMIN_CHATIDS: []
  ```

- **`LOG_USER_TO_APP_LOGS`**:

  If _LOG_USER_TO_APP_LOGS_ is set to `true` then user logs will be appended as part of the bot logs too.

  Bot log file can be found at: `../${rootDir}/logs/${log_file}.log`\
   User specific log files can be found at: `../${rootDir}/users/${userId}/${userId}.log`

  For more information about **logging** go to [3) Logging](#2-states--stages).

&nbsp;

---

&nbsp;

## 1.3) Adding CTF Challenges

The default directory for CTF challenges is at `${rootDir}/ctf/challenges`.

Each challenge is a subdirectory with the following name format:

    {NUMBER}-CHALLENGE_NAME

![challenge_format](docs/img/2022-05-15%2018-08.png)

The number preceeding the challenge name determines the **order** of display of challenges to the user on Telegram.

![challenge_order](docs/img/2022-05-16%2009-38-22.png)

&nbsp;\
**Each** challenge directory is expected to contain a `challenge.yaml` file of the following format:

![challenge_yaml](docs/img/2022-05-15%2019-23.png)

```yaml
# ../${rootDir}/ctf/challenges/1-challenge/challenge.yaml
description: "Can you find the flag in this file?"
additional_info: null
answer: "flag@answer"

points: 40
time_based: null
one_try: false
multiple_choices: null

hints: []

files: []
```

### challenge.yaml fields reference:

- **`description`** : Required [string]

  Challenge text displayed when viewing challenge.

  ```yaml
  description: "Can you find the flag in this file?"
  ```

- **`additional_info`** : Optional [string, null]

  Additional info displayed when viewing the challenge.\
  It will be displayed under the `Notes:` section of the challenge view.

  If you wish to have additional information displayed:

  ```yaml
  additional_info: "Please do not execute the files from this challenge with admin rights."
  ```

  Else:

  ```yaml
  additional_info: null
  ```

- **`answer`** : Required [string]

  The accepted answer of the challenge. Casing will be ignored when validating users answers.\
  Please ensure the answer contains only the following characters: `alphanumeric _ @`.

  ```yaml
  # If answer is preceeded by "flag@..." then a warning will be given
  # to user when their answer does not begin with flag@.
  answer: "flag@answer"t
  ```

- **`points`** : Required [integer]

  The total score for the challenge before deductions. This should reflect the difficulty of the challenge.

  ```yaml
  points: 40
  ```

- **`time_based`** : Optional [integer, null]

  Whether to calculate the score based on time taken to complete challenge.

  If you wish to set the time limit to 300 `seconds`:

  ```yaml
  # Points is calculated by:
  #     (max(time_taken, time_based) / time_based) * challenge_points_after_hints_deduction
  # If time taken to complete challenge exceeds time_based, then a score of 0 is awarded.
  time_based: 300
  ```

  If you don't wish to enable this:

  ```yaml
  time_based: null
  ```

- **`one_try`** : Required [bool]

  Whether to only allow one attempt for the challenge.

  If you wish to only allow the user to attempt the challenge once:

  ```yaml
  one_try: true
  ```

  Else:

  ```yaml
  one_try: false
  ```

- **`multiple_choices`** : Optional [list, null]

  Whether your challenge is a mutliple choice challenge.

  If it, you have to provide the possible OPTIONS:

  ```yaml
  # Points is calculated by:
  #     challenge_points_before_hints_deduction / number_of_attempts
  # Ensure that the correct option matches the CHALLENGE:answer (answer checking ignores casing).
  # You can have as many options as you want.
  # Options will be displayed as rows of 2 when possible.
  multiple_choices:
    - Option One
    - Option Two
    - Option Three
    - Option Four
  ```

  Else:

  ```yaml
  multiple_choices: null
  ```

- **`hints`** : Required [list]

  The list of hints provided for your challenge.

  ```yaml
  hints:
    - text: "Hint here"
      deduction: 5
  ```

  You can have as many hints as needed:

  ```yaml
  hints:
    - text: "Hint One"
      deduction: 5
    - text: "Hint Two"
      deduction: 5
    - text: "Hint Three"
      deduction: 5
  ```

  Or none at all:

  ```yaml
  hints: []
  ```

- **`files`** : Required [list]

  The list of file links to download the files needed for your challenge.

  ```yaml
  files:
    - "https://url-to-file.com"
  ```

  You can have as many file links as needed:

  ```yaml
  files:
    - "https://first-file.com"
    - "https://second-file.com"
    - "https://third-file.com"
  ```

  Or none at all:

  ```yaml
  files: []
  ```

&nbsp;

---

&nbsp;

## 1.4) Running the Chatbot

Before running the chatbot,

1. Please ensure that you have configured `config.yaml` correctly:

   Refer to [this](#12-configuring-configyaml) if you have not done so.

2. Run the project.

   The entry point of the chatbot is `main.py`.

   ```bash
   # cd ${rootDir}

   # Linux:
   $ venv/bin/python main.py
   # Windows:
   $ .\venv\Scripts\python.exe .\main.py
   ```

   Or if you have the virtual env already activated:

   ```bash
   # cd ${rootDir}

   # Linux:
   $ source venv/bin/activate
   $ python main.py
   # Windows:
   $ venv\Scripts\activate.bat
   $ python .\main.py
   ```

   &nbsp;

---

&nbsp;

# 2) STATES & STAGES

Throughout this project, you will see a lot of references to stages and states.\
Below is a brief explanation for them however it does not cover the implementation details behind them.

- A `state` is a condition of outcome that the `User` is in.

  A state is identified as as a unique `integer` hence the user can only be ONE state at any given time.\
  The actual integral value of the state has no meaning other than to signifiy the sequence of instantiation (order of which we defined the states).

  When creating a state, we define a list of `callback handlers` to handle the next input provided by the user and decide on an outcome.

  There are two types of callback handlers:

  1. `CallbackQueryHandler` - called when user presses a given `InlineKeyboardButton` \
     This handler is specific to the button meaning that the `pattern` of the CallbackQueryHandler must match the `callback_data` of the InlineKeyboardButton.

  2. `MessageHandler` - called when user sends a message \
     This handler is non-specific and will be called for every message the user sends. Proper steps must be taken to prevent user from submitting data more than once.

- A `stage` is a essentially a collection of states with added functionality to allow the creation of complex logic. Stages can also be nested within stages allowing the use of inbuilt stages in your custom stages.

  Each stage has:

  1.  An `entry` function.
      This is the function called when loading the stage from another stage in `bot.proceed_next_stage`

  2.  An `exit` function.
      This is an optional callback but good to have if the stage has multiple exit points that leads to the same outcome.

  3.  States
      This is an dictionary of states that the stage can be in.\
       Each state has callback handlers to handle any action done in that state.\

      ```python
        {
            "STATE_NAME" : [
                CallbackQueryHandler(callback_function, pattern=state_pattern, run_async=True),
                MessageHandler(Filters.all, callback_function, run_async=True)
            ],
            ...
        }
      ```

For a more detailed explanation, please refer to the [Implementation Documentation](www.google.com) page.

---

## 2.1) Inbuilt stages

### 2.1.1) let_user_choose

Presents a variable number of choices to the user. The choices are in the form of buttons (ReplyMarkupButton).

```python
# TODO: Document this stuff better
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
    # TODO: Illustrate where this function originate from...
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

### 2.1.2) get_input_from_user

Presents an input field to the user. Input is capture through the next valid message sent from input prompt.

```python
def callback(input_given : str, update : Update, context : CallbackContext) -> USERSTATE:
    print("Input given was:", input_given)
    return Bot.proceed_next_stage(
        current_stage_id="input:example_input",
        next_stage_id=NEXT_STAGE_ID,
        update=update, context=context
    )

example_input = Bot.get_input_from_user(
    input_label="example_input",
    input_text="Please input your \_\_\_\_:",
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

### 2.1.3) get_info_from_user

Similar to `get_input_from_user` except that the input is a user information and is stored globally in the userdata. No additional logic implementation is required.

```python
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

## 2.2) Creating a custom stage

### Example of a stage:

src/stages/example.py

```python
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from bot import (Bot, USERSTATE)
from user import (User, Users)

class Example(object):
    def init(self, bot : Bot):
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

```python
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
BOT_TOKEN = CONFIG["BOT_TOKENS"]["live"]

def main():
    logger = Log(
        name=**name**,
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

if **name** == "**main**":
    main()
```

---

# TECHNICAL DOCUMENTATION
