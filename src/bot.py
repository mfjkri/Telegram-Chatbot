from typing import (Any, Callable, Dict, List, Union)

import telegram
from telegram import (CallbackQuery, ParseMode, ReplyMarkup, Update)
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, CallbackContext)

from user import (UserManager, User)
from utils.log import Log
from stage import (Stage, LetUserChoose, GetInputFromUser,
                   GetInfoFromUser, EndConversation)

# TODO Move this constants to another module
USERSTATE = int
MESSAGE_DIVIDER = "—————————————————————————\n"


class Bot(object):
    def add_state(self, stage_id: str, state_name: str,
                  callbacks: List[Union[CallbackQueryHandler, MessageHandler]]) -> USERSTATE:
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

    def register_stage(self, stage: Stage) -> Dict[str, List[Union[CallbackQueryHandler, MessageHandler]]]:
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

        self.stages.update({stage.stage_id: stage})

        states = {}
        for state_name, callback_handlers in stage._states.items():
            states.update({state_name: self.add_state(
                stage_id=stage.stage_id,
                state_name=stage.stage_id + state_name,
                callbacks=callback_handlers
            )})
        return states

    def unpack_states(self,
                      states: Dict[str, Union[str, CallbackQueryHandler, MessageHandler]]) -> List:
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

    def exit_conversation(self,
                          current_stage_id: str,
                          update: Update, context: CallbackContext) -> USERSTATE:
        return self.proceed_next_stage(
            current_stage_id=current_stage_id,
            next_stage_id=self.end_stage.stage_id,
            update=update, context=context
        )

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
        next_stage: Stage = self.stages.get(
            next_stage_id) if next_stage_id else self.stages.get(self.states[0]["stage_id"])

        if next_stage and user and (not user.is_banned or next_stage_id == self.end_stage.stage_id):
            user.logger.info("PROCEED_NEXT_STAGE",
                             f"User:{user.chatid} is moving on from: {current_stage_id} to: {next_stage_id}")
            return next_stage.stage_entry(update, context)
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

            return self.exit_conversation(
                current_stage_id=current_stage_id,
                update=update, context=context
            )

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
                context.bot.send_message(user.chatid, text,
                                         reply_markup=reply_markup,
                                         parse_mode=parse_mode)
            else:
                self.logger.error("UNKNOWN_TARGET_USER",
                                  "Unknown user to reply message to.")

    def let_user_choose(self,
                        choice_label: str,
                        choice_text: str,
                        choices: List[Dict[str, str]],
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
        stage = LetUserChoose(
            stage_id=stage_id,
            next_stage_id="",
            bot=self)

        stage.setup(
            choice_label=choice_label,
            choice_text=choice_text,
            choices=choices,
            choices_per_row=choices_per_row)

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
        stage = GetInputFromUser(
            stage_id=stage_id,
            next_stage_id="",
            bot=self)

        stage.setup(
            input_label=input_label,
            input_text=input_text,
            input_handler=input_handler,
            exitable=exitable
        )

        return stage_id

    def get_info_from_user(self,
                           data_label: str,
                           next_stage_id: str,
                           input_formatter: Callable = lambda _: _,
                           additional_text: str = None,
                           use_last_saved: bool = True, allow_update: bool = True) -> str:
        """
        In-built function to create a stage that collects a user info (string).
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

        stage_id = f"collect:{data_label}"
        stage = GetInfoFromUser(
            stage_id=stage_id,
            next_stage_id=next_stage_id,
            bot=self)

        stage.setup(
            data_label,
            input_formatter=input_formatter,
            additional_text=additional_text,
            use_last_saved=use_last_saved,
            allow_update=allow_update
        )

        return stage_id

    def conversation_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        if update.message:
            chatid = str(update.message.chat_id)

            cached_user: User = context.user_data.get("user")
            user: User = cached_user or self.user_manager.new(chatid)

            if user:
                context.user_data.update({"user": user})

                return self.proceed_next_stage(
                    current_stage_id="start",
                    next_stage_id=self.first_stage,
                    update=update, context=context
                )

            # An unknown exception was raised.
            return self.proceed_next_stage(
                current_stage_id="start",
                next_stage_id=self.end_stage.stage_id,
                update=update, context=context
            )
        else:
            self.logger.error("USER_MESSAGE_INVALID",
                              f"Unknown user has entered a message with no valid update")

    def end_of_chatbot(self, update: Update, context: CallbackContext) -> None:
        """
        Default function that is called in bot.end_stage.stage_entry, when user reaches end of conversation.

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

    def start(self, live_mode: bool = False) -> None:
        """
        Starts the bot

        :param live_mode: Whether to drop_pending_updates when starting to poll. (Optional, defaults to False)

        :return: None
        """

        self.end_stage: EndConversation = EndConversation(
            stage_id="end",
            next_stage_id=None,
            bot=self
        )
        self.end_stage.setup()

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

        self.user_manager.load_users_from_file()

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

    def init(self, token: str, logger: Log, config: Dict[str, Any]) -> None:
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

        self.user_manager = UserManager()

        self.config = config
        self.bot_config = config["BOT"]
        self.admin_chatids = config.get("ADMIN_CHATIDS", [])
        self.user_passcodes = config.get("USER_PASSCODES", [])

        self.behavior_remove_inline_markup = self.bot_config["REMOVE_INLINE_KEYBOARD_MARKUP"]

        answer_query = telegram.CallbackQuery.answer

        # FIXME Find a better way to override this
        # Maybe do away with overriding it entirely

        def override_answer(query: CallbackQuery,
                            keep_message: Union[bool, str] = False,
                            do_nothing: bool = False,
                            *args) -> None:
            chatid = str(query.message.chat_id)
            user: User = self.user_manager.users.get(chatid)
            if query.id not in user.answered_callback_queries:
                if self.behavior_remove_inline_markup:
                    try:
                        if not do_nothing:
                            if keep_message:
                                if keep_message is True:
                                    query.message.edit_reply_markup()
                                else:
                                    query.message.edit_text(keep_message)
                            else:
                                query.message.edit_text("💭 Loading...")
                    except Exception as e:
                        self.logger.error(False, e)
                answer_query(query, *args)
                user.answered_callback_queries.append(query.id)
        telegram.CallbackQuery.answer = override_answer

    def __new__(cls, *_):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Bot, cls).__new__(cls)
        return cls.instance
