# Table of contents

1. [Quickstart](#1-quickstart-reference)
   - [1.1 Setting up](#11-setting-up):
     - [**setup.py**](#111-setuppy)
     - [Building manually](#112-building-manually)
   - [1.2 Configuring **config.yaml**](#12-configuring-configyaml)
   - [1.3 Adding CTF Challenges](#13-adding-ctf-challenges)
   - [1.4 Running Chatbot](#14-running-the-chatbot)
   - [1.5 Using runtime helper_scripts](#15-using-runtime-helperscripts)
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
# For example, if your system uses python3:
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

   # -------------------------------- BOT CONFIG -------------------------------- #
   BOT_TOKENS:
     LIVE: BOT_TOKEN
     TEST: BOT_TOKEN

   BOT:
     REMOVE_INLINE_KEYBOARD_MARKUP: True

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

# -------------------------------- BOT CONFIG -------------------------------- #
BOT_TOKENS:
  LIVE: BOT_TOKEN
  TEST: BOT_TOKEN

BOT:
  REMOVE_INLINE_KEYBOARD_MARKUP: True

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

- **`BOT`**:

  If **REMOVE_INLINE_KEYBOARD_MARKUP** is set to `true` then the bot will remove InlineKeyboardMarkup for its previous message everytime an InlineKeyboardButton is pressed (handled through the query.answer callback that is called after the event is triggered). This is to prevent users from using old menu buttons however can cause visual confusion to user due to multiple updates to dislay messages (first Remove keyboard-markup then update message content to new text).

- **`USER_PASSCODES`**:

  **Note:** This field is only used with [`Stage:Authenticate`](src/stages/authenticate.py). If you are not using the stage, you can ignore this field.

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

  **Note:** This field is only used with [`Stage:Admin`](src/stages/admin.py). If you are not using the stage, you can ignore this field.

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

1. Ensure [`config.yaml`](config.yaml) is configured correctly.

   Please refer to [this](#12-configuring-configyaml) if you have not done so.

2. Run the project.

   The entry point of the chatbot is `main.py`.

   With `venv` activated for your terminal session:

   - Activating venv:

     ```bash
     # cd ${rootDir}

     # Linux:
     $ source venv/bin/activate

     #Windows:
     $ venv\Scripts\activate.bat
     ```

   - Running main.py:

     ```bash
     # cd ${rootDir}

     # Linux:
     $(venv) python main.py

     # Windows:
     $(venv) python .\main.py
     ```

   Or if you don't wish or can't get venv activated:

   ```bash
   # cd ${rootDir}

   # Linux:
   $ venv/bin/python main.py

   # Windows:
   $ .\venv\Scripts\python.exe .\main.py
   ```

&nbsp;

---

&nbsp;

## 1.5) Using runtime helper_scripts

`Warning: Do not use the helper scripts unless you know what you are doing.`\
`Some scripts can cause irrevisble changes to your project.`

Helper scripts are scripts that are designed to be used either before, during or after a session of [running](main.py) the Telegram Bot.

They help to make your life easier by executing common tasks or tasks that are repetitive and can be automated or even help you out in testing and debugging of the bot.

Scripts that are ran before a session include:

- [`create_fake_users`](src/helper_scripts/create_fake_users.py)
- [`create_placeholder_challenges`](src/helper_scripts/create_placeholder_challenges.py)
- [`generate_passcodes`](src/helper_scripts/generate_passcodes.py)

Scripts that are ran during a session include:

- [`leaderboard`](src/helper_scripts/leaderboard.py)

Scripts that are ran after a session include:

- [`notify_winners`](src/helper_scripts/notify_winners.py)
- [`export_logs`](src/helper_scripts/export_logs.py)

&nbsp;

Below is a brief description of what each script does and how to use them.

- [`ban_all_users`](/src/helper_scripts/ban_all_users.py):

  This script will get all the existing users found in the [users directory](/users/) and add their chatids to the [banned_users.yaml](/users/banned_users.yaml) file. It will NOT DELETE their files, if you wish to do that, you will have to it manually.

  It is useful for preventing users from an earlier session from joining in on a later session.

  Usage:

  ```bash
  # Replace python with your system python keyword
  # Replace the forward slash with backslash for Windows
  $ python src/helper_scripts/ban_all_users.py
  ```

- [`create_fake_users`](/src/helper_scripts/create_fake_users.py):

  This script will generate fake users that will "attempt" and "complete" some of the existing CTF challenges.

  It is useful for populating the leaderboard during testing and also for creating test export log files (more on that below).

  Currently the fake users are only configured to attempt CTF Challenges and not any other stages such as [Guardian](src/stages/guardian.py).

  Arguments:

  ```
  $ python src/helper_scripts/create_fake_users.py -h
  usage: create_fake_users.py [-h] [-n N] [-c C]

  optional arguments:
    -h, --help  show this help message and exit
    -n N        Number of users to generate. Max is 26. If set to 0 then max will be taken.
    -c C        Number of challenges to attempt per user.
  ```

  Usage:

  ```bash
  # Replace python with your system python keyword
  # Replace the forward slash with backslash for Windows
  $ python src/helper_scripts/create_fake_users.py -n 20 -c 4
  ```

  `-n` argument is for the number of fake users to create. It is capped at 26.

  `-c` argument is for the number of challenges to attempt per user. It will be capped at the number of current existing CTF challenges.

- [`create_placeholder_challenges`](/src/helper_scripts/create_placeholder_challenges.py):

  This script will create placeholder challenges either based on the in-built challenge.yaml template or using a provided file.

  It is useful for testing purposes and removing the need to update challenges manually everytime when testing a new feature.

  **Warning**: This script **WILL DELETE ALL** current challenges found in the [challenges directory](/ctf//challenges/).

  Arguments:

  ```
  $ python src/helper_scripts/create_placeholder_challenges.py -h
  usage: create_placeholder_challenges.py [-h] [-i I] [-n N]

  optional arguments:
    -h, --help  show this help message and exit
    -i I        challenge.yaml input file as template
    -n N        Number of challenges to generate. If omitted, defaults to 4.
  ```

  Usage:

  ```bash
  # Replace python with your system python keyword
  # Replace the forward slash with backslash for Windows
  $ python src/helper_scripts/create_placeholder_challenges.py -n 10
  ```

  `-i` argument is for providing a custom challenge.yaml to use as template when creating the placeholder challenges.

  `-n` argument is for the number of placeholder challenges to create.

- [`export_logs`](/src/helper_scripts/export_logs.py):

  This script will generate a [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) file that can be imported into Excel for visualization of users data.

  It will only extract from the user logs, actions that are relevant to their scoring such as:

  - Viewing of hints
  - Attempting the challenge
  - Completing the challenge

  Arguments:

  ```
  $ python src/helper_scripts/export_logs.py -h
  usage: export_logs.py [-h] [-o O] [-u U] [-g G]

  optional arguments:
    -h, --help  show this help message and exit
    -o O        File name to output exported logs to. Defaults to exported_logs.
    -u U        Specify a chatid to export logs from.
    -g G        Specify a group to export logs from.
  ```

  Usage:

  ```bash
  # Replace python with your system python keyword
  # Replace the forward slash with backslash for Windows
  $ python src/helper_scripts/export_logs.py -o "example_export"
  ```

  `-o` argument is for the exported csv filename. The ".csv" file extension should not be included in the argument

  `-u` argument is for if you want to export logs from only one user (provide the chatid here).

  `-g` argument is for if you want to export logs from only one user group (provide group name here).

---

&nbsp;

# 2) STATES & STAGES

Throughout this project, you will see a lot of references to stages and states.\

Simply said, a `state` is the smallest unit of "building block" while a `stage` is a group of states (or nested stages even) with its inner functionality abstracted away for either reduced code duplication or means of organization.

With the use of stages you can reuse common functionality between stages, see [in-built stages](#21-inbuilt-stages).\
You can also create custom stages to have unique functionality, see [custom stages](src/stages/).

Below is a more in-depth description however you might find it still insufficient. It is best to dive in and [try it yourself](#22-creating-a-custom-stage).

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

&nbsp;

## 2.1) Inbuilt stages

&nbsp;

### 2.1.1) **let_user_choose**

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

&nbsp;

### 2.1.2) **get_input_from_user**

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

&nbsp;

### 2.1.3) **get_info_from_user**

Similar to `get_input_from_user` except that the input is a user information (string) and is stored globally in the userdata. No additional logic implementation is required.

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

&nbsp;

## 2.2) Creating a custom stage

&nbsp;

### Prequisites:

Creating custom stages will require you to have knowledge about working with [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot/)

Do read more and understand the [examples](https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples) before continuing.\
The relevant examples are: [ConversationBot](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py) and [ConversationBot2](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot2.py).

In our application, `USERSTATE` is a created data-type with an integral value to signify the state of the CallbackHandler.\
`GENDER, PHOTO, LOCATION, BIO ` (found in [ConversationBot](https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py) are examples of USERSTATE in our application.

&nbsp;

### Custom stage (`Example`):

[src/stages/example_stage.py](src/stages/)

```python

```

&nbsp;

### Using custom stage:

[main.py](main.py)

```python
# shebang
import sys
sys.path.append("src")

import logging
import os

from bot import Bot
from user import UserManager, User
import utils.utils as utils
from utils.log import Log

from stages.example_stage import Example

LOG_FILE = os.path.join("logs", f"examplebot.log")

CONFIG = utils.load_yaml_file(os.path.join("config.yaml"))
LIVE_MODE = CONFIG["RUNTIME"]["LIVE_MODE"]
FRESH_START = CONFIG["RUNTIME"]["FRESH_START"] if not LIVE_MODE else False
BOT_TOKEN = CONFIG["BOT_TOKENS"]["LIVE"] if LIVE_MODE else CONFIG["BOT_TOKENS"]["TEST"]


def setup():
    utils.get_dir_or_create(os.path.join("logs"))
    if FRESH_START:
        # Remove runtime files (logs, users, etc)
        pass


def main():
    setup()

    logger = Log(
        name=__name__,
        stream_handle=sys.stdout,
        file_handle=LOG_FILE,
        log_level=logging.DEBUG
    )

    users = UserManager()
    users.init(logger)

    bot = Bot()
    bot.init(BOT_TOKEN, logger)

    STAGE_EXAMPLE = "example"
    STAGE_END = "end"

    # Stage example
    example: Example = Example(bot)
    example.setup(
        stage_id=STAGE_EXAMPLE,         # This stage id is example
        next_stage_id=STAGE_END
    )

    # Start Bot
    bot.set_first_stage(STAGE_EXAMPLE)
    bot.set_end_of_chatbot(
        lambda update, context: bot.edit_or_reply_message(
            update, context, "You have exited the conversation. \n\nUse /start to begin a new one.")
    )
    bot.start(live_mode=LIVE_MODE)


if __name__ == "__main__":
    main()

```
