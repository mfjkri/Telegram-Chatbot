from calendar import c
import time
from typing import (Any, Callable, Union)

from telegram import (InlineKeyboardButton,
                      InlineKeyboardMarkup, ParseMode, ReplyMarkup, Update)
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, CallbackContext, Filters)

import utils.utils as utils
from user import UserManager, User
from utils.log import Log

USERSTATE = int
MESSAGE_DIVIDER = "—————————————————————————\n"


class Bot(object):
    def add_state(self, stage_id: str, state_name: str, callbacks: list) -> USERSTATE:
        """
        Internal private function to add a state to bot's states.
        This function is normally called from Bot.add_stage.

        :param stage_id: Stage identifier, this is the unique name of the stage that the state is part of. (Required)
        :param state_name: State identifier, this is the name of the state. (Required)
        :param callbacks: List of the callback handlers that are active during the state. (Required)
            callbacks = [
                CallbackQueryHandler(...),
                CallbackQueryHandler(...),
                MessageHandler(...)
            ]

        :return: Returns a USERSTATE that is associated with the created state.
        """

        new_state = {
            "name": state_name,
            "stage_id": stage_id,
            "callbacks": callbacks
        }
        self.states.append(new_state)
        return len(self.states) - 1

    def add_stage(self, stage_id: str, entry: Callable, exit: Callable, states: dict) -> dict:
        """
        Helper function to create a stage.
        Use this in your custom_stage.setup to create your stage and add it to the global stages.

        :param stage_id: Stage identifier, this is the unique name of your stage. (Required)
        :param entry: The function called when the stage is being loaded (either from another stage or from /start) (Required)
        :param exit: A function that is useful to have logic for, but it is not accessed outside of the stage logic. (Required)
        :param states: States of the stage which also contains any handlers needed. (Required)
            states = {
                "STATE_ONE" = [
                    CallbackQueryHandler(...)
                ],
                "STATE_TWO" = [
                    MessageHandler(...),
                    CallbackQueryHandler(...)
                ]
            }

        :return: Returns the stage as a dictionary.
        """

        states_dict = {}

        for state_name, callback_handlers in states.items():
            states_dict.update({state_name: self.add_state(
                stage_id=stage_id,
                state_name=stage_id + state_name,
                callbacks=callback_handlers
            )})

        self.stages.update({stage_id: {
            "entry": entry,
            "exit": exit,
            "states": states_dict
        }})

        return self.stages.get(stage_id)

    def add_custom_stage_handler(self, stage_handler: Any) -> None:
        """
        Helper function to add handler for a given custom stage.
        The handler callback is called in Bot.start (right after users data have been loaded from file)

        :param stage_handler: Callable function handler. (Required)

        :return: Returns None.
        """

        self.stages_handlers.append(stage_handler)

    def unpack_states(self, states: dict) -> list:
        """
        Helper function to unpack states.
        Converts the states dictionary into an ordered list which can later be unpacked.
        The variables have to be in the same order that the states was created in.

            states = {"stateA" : ..., "stateB" : ...}
            stateA, stateB = unpack_states(states)

        :param states: States to unpack. (Required)

        :return: Returns a list of states which can be unpacked.
        """

        states_list = []

        for state_name, state in states.items():
            states_list.append(state)

        return states_list

    def proceed_next_stage(self,
                           current_stage_id: str,
                           next_stage_id: Union[str, None],
                           update: Update, context: CallbackContext) -> USERSTATE:
        """
        Helper function to proceed from one stage to the next.
        Calls the entry function of the next stage.

        :param current_stage_id: Caller's stage stage_id. (Required)
        :param next_stage_id: Stage_id of the next stage to proceed to. (Required)
            If next_stage_id is None, then it will load the stage of the very first state that was defined.
            If next_stage_id is not found, then it will proceed to the end of the conversation.
        :param update: Update passed from caller function. (Required)
        :param context: Context passed from caller function. (Required)

        :return: Returns the USER_STATE of the new active stage.
        """

        user: User = context.user_data.get("user")
        next_stage = self.stages.get(
            next_stage_id) if next_stage_id else self.stages.get(self.states[0]["stage_id"])

        if next_stage and user and not user.is_banned:
            user.logger.info("PROCEED_NEXT_STAGE",
                             f"User:{user.chatid} is moving on from: {current_stage_id} to: {next_stage_id}")
            return next_stage["entry"](update, context)
        else:
            if not user:
                chatid, _ = context._user_id_and_data
                self.logger.error("USER_NOT_REGISTERED",
                                  f"User:{chatid} not found in users. Current stage: {current_stage_id}")
                self.edit_or_reply_message(
                    update, context,
                    text="<b>ERROR</b>: Unknown user.\n\n"
                    "If you are seeing this, please contact your System Administrator."
                )
            elif user.is_banned:
                user.logger.error("USER_BANNED",
                                  f"User:{user.chatid} is a banned user. Current stage: {current_stage_id}")

                self.edit_or_reply_message(
                    update, context,
                    text="Unfortunately, it appears you have been <b>banned</b>.\n\n"
                    "If you believe this to be a mistake, please contact the System Administrator."
                )
            elif not next_stage:
                user.logger.error("NEXT_STAGE_MISSING",
                                  f"User:{user.chatid} is proceeding to unknown next stage: {next_stage_id}. Current stage: {current_stage_id}")

                self.edit_or_reply_message(
                    update, context,
                    text="<b>ERROR</b>: Unknown next stage.\n\n"
                    "If you are seeing this, please contact your System Administrator."
                )

            return self.stages.get("end")["entry"](update, context)

    def edit_or_reply_message(self,
                              update: Update, context: CallbackContext,
                              text: str,
                              reply_markup: ReplyMarkup = None,
                              parse_mode: ParseMode = ParseMode.HTML,
                              reply_message: bool = False) -> None:
        """
        Helper function to edit or reply the message sent by bot with new text and reply_markup.

        :param update: Update passed from caller function. (Required)
        :param context: Context passed from caller function. (Required)
        :param text: Text to edit or reply message with. (Required)
        :param reply_markup: Reply_markup to append with the message. (Optional, Defaults to None)
        :param parse_mode: ParseMode to format the message with. (Optional, Defaults to ParseMode.HTML)
        :param reply_message: Whether it should edit or reply to its previous message

        :return: None
        """

        user: User = context.user_data.get("user")

        if update.callback_query and not reply_message:
            update.callback_query.message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        elif update.message:
            update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        else:
            if user:
                context.bot.send_message(user.chatid, text)
            else:
                self.logger.error("UNKNOWN_TARGET_USER",
                                  "Unknown user to reply message to.")

    def let_user_choose(self,
                        choice_label: str,
                        choice_text: str,
                        choices: list,
                        choices_per_row: Union[int, None] = None) -> str:
        """
        In-built function to create a stage that presents the user with a series of choices.
        stage_id of the stage created is of the format {choose:CHOICE_LABEL}

        :param choice_label: The choice label of the decision to be made by user (for example: participate_in_something). Will also be appended in the stage_id. (Required)
        :param choice_text: The text displayed when prompting user to choose. (Required)
        :param choices: A list of the choices that is available to be made by user. (Required)
            choices = [
                {
                    "text" : THIS_CHOICE_TEXT,
                    "callback" : CALLBACK_FUNCTION_HERE
                },
            ]
        :param choices_per_row: How many choices to have in a row. If None, then all choices will be on the same row. (Optional, Defaults to None)

        :return: Returns the stage_id of the stage created.
        """

        stage_id = f"choose:{choice_label}"
        CHOICE_CONFIRMATION = None
        callbacks, keyboard = [], [[]]

        for idx, choice in enumerate(choices):
            if choices_per_row and idx % choices_per_row == 0:
                keyboard.append([])
            callbacks.append(CallbackQueryHandler(
                choice["callback"], pattern=f"^{choice_label}:choice:{idx}$", run_async=True))
            keyboard[-1].append(InlineKeyboardButton(choice["text"],
                                callback_data=f"{choice_label}:choice:{idx}"))

        def prompt_entry(update: Update, context: CallbackContext) -> USERSTATE:
            query = update.callback_query
            if query:
                query.answer()

            self.edit_or_reply_message(
                update, context,
                choice_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return CHOICE_CONFIRMATION

        stage = self.add_stage(
            stage_id=stage_id,
            entry=prompt_entry,
            exit=None,
            states={
                choice_label + "confirmation": callbacks
            }
        )
        states = stage["states"]
        CHOICE_CONFIRMATION = self.unpack_states(states)[0]
        return stage_id

    def get_input_from_user(self,
                            input_label: str,
                            input_text: str,
                            input_handler: Callable,
                            exitable: bool = False) -> str:
        """
        In-built function to create a stage that collects a user input.
        stage_id of the stage created is of the format {input:INPUT_LABEL}

        :param input_label: The input label of the input sent by user (for example: answer). Will also be appended in the stage_id. (Required)
        :param input_text: The text displayed before prompting to enter their input. (Required)
        :param input_handler: A callback function that is called with the user input. (Required)
            input_handler(input : str, update : Update, context : Context)
        :param exitable: Whether to allow the user to abort the input by sending /cancel. (Optional, Defaults to False)

        :return: Returns the stage_id of the stage created.
        """

        stage_id = f"input:{input_label}"
        INPUT_MESSAGE_HANDLER = None
        debounce = True

        def prompt_input(update: Update, context: CallbackContext) -> USERSTATE:
            nonlocal debounce

            query = update.callback_query
            if query:
                query.answer()

            self.edit_or_reply_message(
                update, context,
                input_text
            )

            debounce = False

            return INPUT_MESSAGE_HANDLER

        def message_handler(update: Update, context: CallbackContext) -> USERSTATE:
            nonlocal debounce
            if not debounce and update.message:
                debounce = True
                if utils.format_input_str(update.message.text, False, "/cancel") == "/cancel" and exitable:
                    return self.conversation_exit(update, context)
                else:
                    return input_handler(update.message.text, update, context)

        stage = self.add_stage(
            stage_id=stage_id,
            entry=prompt_input,
            exit=None,
            states={
                input_label + "message_handler": [MessageHandler(Filters.all, message_handler, run_async=True)]
            }
        )
        states = stage["states"]
        INPUT_MESSAGE_HANDLER = self.unpack_states(states)[0]
        return stage_id

    def get_info_from_user(self,
                           data_label: str,
                           next_stage_id: str,
                           input_formatter: Callable = lambda _: _,
                           additional_text: str = None,
                           use_last_saved: bool = True, allow_update: bool = True) -> str:
        """
        In-built function to create a stage that collects a user info.
        stage_id of the stage created is of the format {collect:DATA_LABEL}

        :param data_label: The information label of the data collected from user (for example: name). Will also be appended in the stage_id. (Required)
        :param next_stage_id: The stage_id of the stage to proceed to after successfully completing this stage. (Required)
        :param input_formatter: A callback function that is used to format the input given by user. (Optional, Defaults to an empty callback)
            input_formatter(input : Union[str, bool]) -> if type(input) is Bool [Return expected_format] else return check_input_format(input)

            def input_formatter(input : Union[str, bool]):
                if str is True:
                    return "EXPECTED INPUT FORMAT"
                else:
                    return check_input_format(inputs)

        :param additional_text: Additional text to display when prompting user for info. (Optional, Defaults to None)
        :use_last_saved: Whether to consider previously set value for the info before prompting user wehter to update or just overwrite. (Optional, Defaults to True)
        :allow_update: Whether to allow the user to update the value of the info once set. (Optional, Defaults to True)

        :return: Returns the stage_id of the stage created.
        """
        debounce = True
        stage_id = f"collect:{data_label}"
        INPUT_HANDLER, INPUT_CONFIRMATION = None, None

        confirm_input_pattern = f"collect:{data_label}:confirm"
        retry_input_pattern = f"collect:{data_label}:retry"

        def prompt_entry(update: Update, context: CallbackContext) -> USERSTATE:
            query = update.callback_query
            if query:
                query.answer()

            nonlocal debounce

            user: User = context.user_data.get("user")
            saved_data = user.data.get(data_label)

            if saved_data and saved_data != "" and use_last_saved:
                if allow_update:
                    user.logger.info("USER_DATA_INPUT_UPDATE_PROMPT",
                                     f"User:{user.chatid} is choosing whether to update input({data_label})")

                    context.user_data.update(
                        {f"input:{data_label}": saved_data})

                    text = f"Confirm your <b><u>{data_label}</u></b>:\n\n"
                    text += f"<i>{additional_text}</i>\n\n" if additional_text else ""
                    text += MESSAGE_DIVIDER
                    text += f"<b>{saved_data}</b>\n"
                    text += MESSAGE_DIVIDER + "\n"
                    text += "Press Yes to confirm or No to re-enter."

                    self.edit_or_reply_message(
                        update, context,
                        text=text,
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(
                                    "Yes", callback_data=confirm_input_pattern),
                                InlineKeyboardButton(
                                    "No", callback_data=retry_input_pattern),
                            ]
                        ]),
                    )

                    return INPUT_CONFIRMATION
                else:
                    user.logger.info("USER_DATA_INPUT_UPDATE_FORBIDDEN",
                                     f"User:{user.chatid} is forbidden from updating input({data_label}). Using old value...")
                    return prompt_exit(update, context)
            else:
                user.logger.info("USER_DATA_INPUT_INIT_PROMPT",
                                 f"User:{user.chatid} is choosing input({data_label})")
                self.edit_or_reply_message(
                    update, context,
                    text=f"Please enter your <b>{data_label}</b>:" +
                    (f"\n\n<i>{additional_text}</i>" if additional_text else " ")
                )
                debounce = False
                return INPUT_HANDLER

        def prompt_exit(update: Update, context: CallbackContext) -> USERSTATE:
            return self.proceed_next_stage(stage_id, next_stage_id, update, context)

        # --
        def input_handler(update: Update, context: CallbackContext) -> USERSTATE:
            nonlocal debounce

            if not debounce and update.message is not None:
                debounce = True

                user: User = context.user_data.get("user")

                user_input = update.message.text
                formatted_user_input = input_formatter(user_input)

                if user_input == "cancel":
                    return self.proceed_next_stage(stage_id, "end", update, context)
                # elif user_input == "/start":
                    # return self.proceed_next_stage(stage_id, None, update, context)

                if formatted_user_input:
                    user.logger.info("USER_DATA_INPUT_CONFIRMATION",
                                     f"User:{user.chatid} entered an input({data_label}) of @{user_input}@")

                    context.user_data.update(
                        {f"input:{data_label}": formatted_user_input})

                    self.edit_or_reply_message(
                        update, context,
                        text=f"Is your {data_label}: <b>{formatted_user_input}</b>?\n\nPress Yes to confirm or No to re-enter.",
                        reply_markup=InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton(
                                    "Yes", callback_data=confirm_input_pattern),
                                InlineKeyboardButton(
                                    "No", callback_data=retry_input_pattern),
                            ]
                        ])
                    )

                    return INPUT_CONFIRMATION
                else:
                    user.logger.warning("USER_DATA_INPUT_WRONG_FORMAT",
                                        f"User:{user.chatid} entered an input({data_label}) of the wrong format. @{user_input}@")

                    text = f"Your input: <b>{user_input}</b> is invalid."
                    expected_input_format = input_formatter(True)
                    if expected_input_format is not True:
                        text += f"\n\nExpected format: {expected_input_format}"

                    self.edit_or_reply_message(
                        update, context,
                        text=text
                    )
                    return prompt_entry(update, context)

        def confirm_input(update: Update, context: CallbackContext) -> USERSTATE:
            query = update.callback_query
            query.answer()

            user: User = context.user_data.get("user")
            user.logger.info("USER_DATA_INPUT_CONFIRMED",
                             f"User:{user.chatid} confirmed an input({data_label})")
            user.update_user_data(
                data_label, context.user_data[f"input:{data_label}"])

            self.edit_or_reply_message(
                update, context,
                "💭 Loading..."
            )
            time.sleep(0.25)

            return prompt_exit(update, context)

        def retry_input(update: Update, context: CallbackContext) -> USERSTATE:
            query = update.callback_query
            query.answer()

            nonlocal debounce

            user: User = context.user_data.get("user")
            user.logger.info("USER_DATA_INPUT_RETRY",
                             f"User:{user.chatid} retrying an input({data_label})")

            self.edit_or_reply_message(
                update, context,
                f"Please enter your <b>{data_label}</b>:"
            )
            debounce = False
            return INPUT_HANDLER
        # --

        stage = self.add_stage(
            stage_id=f"collect:{data_label}",
            entry=prompt_entry,
            exit=prompt_exit,
            states={
                data_label + "input_handler": [
                    MessageHandler(Filters.all, input_handler, run_async=True)
                ],
                data_label + "confirmation": [
                    CallbackQueryHandler(
                        retry_input, pattern=f"^{retry_input_pattern}$", run_async=True),
                    CallbackQueryHandler(
                        confirm_input, pattern=f"^{confirm_input_pattern}$", run_async=True),
                ]
            }
        )
        states = stage["states"]
        INPUT_HANDLER, INPUT_CONFIRMATION = self.unpack_states(states)

        self.users.add_data_field(data_label, "")
        return stage_id

    def end_of_chatbot(self, update: Update, context: CallbackContext) -> None:
        """
        Default function that is called in conversation_exit, when user reaches end of conversation.

        :param update: (Required)
        :param context: (Required)

        :return: None
        """

        self.edit_or_reply_message(
            update, context,
            text="Find out more about what we do at www.csa.gov.sg!"
            "\n\nUse /start to resume where you left off.",
            reply_message=True
        )

    def conversation_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        if update.message:
            chatid = str(update.message.chat_id)

            cached_user: User = context.user_data.get("user")
            user: User = cached_user or self.users.new(chatid)

            if user:
                if not cached_user:
                    context.user_data.update({"user": user})

                return self.proceed_next_stage(
                    current_stage_id="start",
                    next_stage_id=self.first_stage,
                    update=update, context=context
                )
            else:
                # User has been banned
                return self.proceed_next_stage(
                    current_stage_id="start",
                    next_stage_id="end",
                    update=update, context=context
                )
        else:
            self.logger.error("USER_MESSAGE_INVALID",
                              f"Unknown user has entered a message with no valid update")

    def conversation_exit(self, update: Update, context: CallbackContext) -> USERSTATE:
        user: User = context.user_data.get("user")
        if user:
            user.logger.info("USER_REACHED_END_OF_CONVERSATION",
                             f"User:{user.chatid} has reached the end of the conversation")
        else:
            self.logger.info("UNREGISTERED_USER_END_OF_CONVERSATION",
                             f"Unregistered or banned user has reached the end of the conversation")

        self.end_of_chatbot(update, context)
        return ConversationHandler.END

    def start(self, live_mode: bool = False) -> None:
        """
        Starts the bot

        :param live_mode: Whether to drop_pending_updates when starting to poll. (Optional, defaults to False)

        :return: None
        """
        self.add_stage("end", entry=self.conversation_exit,
                       exit=None, states={})

        conversation_states = {}
        for idx, state in enumerate(self.states):
            conversation_states.update({idx: state["callbacks"]})

        start_command = CommandHandler(
            "start", self.conversation_entry, run_async=True)
        self.dispatcher.add_handler(
            ConversationHandler(
                entry_points=[start_command],
                states=conversation_states,
                fallbacks=[start_command],
                per_message=False,
                allow_reentry=True,
                run_async=True
            )
        )

        self.users.load_users_from_file()

        for handlers in self.stages_handlers:
            init_callback = getattr(handlers, "init_with_users_loaded", None)
            if init_callback:
                init_callback()

        self.logger.info(False, '-')
        self.logger.info(False, "Bot is now listening!")
        self.logger.info(False, '-')

        self.updater.start_polling(drop_pending_updates=live_mode)
        self.updater.idle()

    def set_first_stage(self, stage_id: str) -> None:
        """
        Sets the starting stage for the bot (stage to proceed right after User sends the /start command).

        :param stage_id: Stage identifier string of the starting stage. (Required)
        :return: None
        """

        self.first_stage = stage_id

    def set_end_of_chatbot(self, end_of_chatbot: Callable) -> None:
        """
        Overrides the default bot.end_of_chatbot with a custom one.

        :param end_of_chatbot: Custom function to replace default end_of_chatbot (Required)
        :return: None
        """
        self.end_of_chatbot = end_of_chatbot

    def init(self, token: str, logger: Log) -> None:
        """
        Initializes the Bot class.

        :param token: Token string for your TelegramBot. (Required)
        :param logger: Logger object to use for logging purposes by the bot. (Required)

        :return: None
        """
        self.logger = logger
        self.token = token

        updater = Updater(token)
        dispatcher = updater.dispatcher

        self.stages = {}
        self.states = []

        self.first_stage = None

        self.updater = updater
        self.dispatcher = dispatcher

        self.users = UserManager()
        self.stages_handlers = []

    def __new__(cls, *_):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Bot, cls).__new__(cls)
        return cls.instance
