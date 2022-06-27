from typing import (Any, Callable, Dict, List, Union, Optional)

import telegram
from telegram import (CallbackQuery, ParseMode, ReplyMarkup, Update)
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          CallbackQueryHandler, MessageHandler, CallbackContext)

from constants import USERSTATE
from user import (UserManager, User)
from utils.log import Log
from stage import (Stage, LetUserChoose, GetInputFromUser,
                   GetInfoFromUser, EndConversation)


class Bot(object):
    """
    TODO Fill up class descriptor
    This object represents the base wrapper 

    Parameters:
        -

        Please read the `Notes` section below.

    Notes:
        The initialization of this class has been moved from the dunder method \
            `__init__` instead to a method: `Bot.init`.

        >>> bot = Bot()
            bot.init(
                token="...",
                logger=logger,
                config=config
            )

        This is due to `Bot` being a `Singleton` class, we would want to prevent \
            multiple initialization of the class object. 

    Attributes:
        TODO Fill up attributes descriptor
        logger (:class:`Log`):
        token (:obj:`str`):

        updater (:class:`Updater`):
        dispatcher (:class:`Dispatcher`): 

        stages (:class:`Dict[str, Stage]`):
        states (:class:`List[Dict]`):

        first_stage (:class:`Stage`): 
        end_stage (:class:`EndConversation`): 

        user_manager (:class:`UserManager`):

        config (:class:`Dict[str, Any]`):  
        bot_config (:class:`Dict[str, Any]`):  
        admin_chatids (:class:`List[str]`):  
        anonymous_user_passcodes (:obj:`bool`):  
        user_passcodes (:class:`List[str]`):  
    """

    def add_state(self, stage_id: str, state_name: str,
                  callbacks: List[Union[CallbackQueryHandler, MessageHandler]]) -> USERSTATE:
        """
        Internal private function to add a state to bot's states.

        This function is normally called from `@bot.register_stage`.

        Parameters:
            stage_id (:obj:`str`): Unique identifier of the stage that the state is in.
            state_name (:obj:`str`): Non-unique identifier of the state, only used for debugging.
            callbacks (:class:`List`): List of callback handlers that are active during the state.

        Returns:
            (:class:`USERSTATE`): Returns a USERSTATE that is associated with the created state.

        Example:
            >>> bot.add_state(
                    stage_id="...",
                    state_name="...",
                    callbacks = [
                        CallbackQueryHandler(...),
                        CallbackQueryHandler(...),
                        MessageHandler(...)
                    ]
                )
        """

        new_state = {
            "name": state_name,
            "stage_id": stage_id,
            "callbacks": callbacks
        }
        self.states.append(new_state)
        return len(self.states) - 1

    def get_stage_from_id(self, stage_id: str) -> Union[Stage, None]:
        """
        Helper function to retrieve a registered stage from its stage_id.

        All registered stages can be found in `bot.stages` (indexed using their `stage_id`).

        Parameters:
            stage_id (:obj:`str`): Unique identifier of the target stage.

        Returns:
            (:class:`Stage`|:obj:`None`): Returns the target stage object if found, else returns None.

        Example:
            >>> target_state: Stage  = bot.get_stage_from_id(
                    stage_id="..."
                )
        """

        return self.stages.get(stage_id, None)

    def register_stage(self, stage: Stage) -> None:
        """
        Helper function to register a stage.

        Call this function from within your `custom_stage.setup()` method to register the `custom_stage`\
            as an active stage of the bot.

        Parameters:
            stage (:class:`Stage`): Instantiated object of type stage

        Returns:
            (:obj:`None`)

        Example:
            >>> class CustomStage(Stage):
                    ...
                    def setup(...) -> None:
                        ...
                        self.states = {...}
                        self.bot.register_stage(
                            stage=self
                        )
                        ...
                    ...
        """

        if stage.stage_id not in self.stages:
            self.stages.update({stage.stage_id: stage})

            states = {}
            for state_name, callback_handlers in stage.states.items():
                states.update({state_name: self.add_state(
                    stage_id=stage.stage_id,
                    state_name=stage.stage_id + state_name,
                    callbacks=callback_handlers
                )})

            stage.states = states
        else:
            self.logger.warning("STAGE_ID_ALREADY_EXISTS",
                                f"Stage ID: {stage.stage_id} already exists as a registered stage.")

    def exit_conversation(self,
                          current_stage_id: str,
                          update: Update, context: CallbackContext) -> USERSTATE:
        """
        Helper function to end the conversation.

        Call this function to immediately proceed to the `end_stage`.

        Parameters:
            current_stage_id (:obj:`str`): Unique identifier of the caller stage.
            update (:class:`Update`): Update passed from the caller function.
            context (:class:`CallbackContext`): Context passed from the caller function.

        Returns:
            (:class:`USERSTATE`): Returns a USERSTATE that is associated with the end stage (`-1`).

        Example:
            >>> def some_callback(self, update: Update, context: CallbackContext) -> USERSTATE:
                    return bot.exit_conversation(
                        current_stage_id=self.stage_id,
                        update=update, context=context
                    )
        """

        return self.proceed_next_stage(
            current_stage_id=current_stage_id,
            next_stage_id=self.end_stage.stage_id,
            update=update, context=context
        )

    def proceed_next_stage(self,
                           current_stage_id: str,
                           next_stage_id: Optional[str],
                           update: Update, context: CallbackContext) -> USERSTATE:
        """
        Helper function to proceed from one stage to the next.

        Calls the `entry function` of the next stage.

        Parameters:
            current_stage_id (:obj:`str`): Unique identifier of the caller stage.
            next_stage_id (:obj:`str`): Optional. Unique identifier of the target stage. Defaults to `bot.first_stage.stage_id`.
            update (:class:`Update`): Update passed from the caller function.
            context (:class:`CallbackContext`): Context passed from the caller function.

        Returns:
            (:class:`USERSTATE`): Returns a USERSTATE that is returned by the `entry` function of the target stage.

        Example:
            >>> def some_callback(self, update: Update, context: CallbackContext) -> USERSTATE:
                    return bot.proceed_next_stage(
                        current_stage_id=self.stage_id,
                        next_stage_id="...",
                        update=update, context=context
                    )
        """

        user: User = context.user_data.get("user")
        next_stage_id = next_stage_id or self.first_stage.stage_id
        next_stage: Stage = self.stages.get(next_stage_id)

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
                              reply_markup: Optional[ReplyMarkup] = None,
                              parse_mode: Optional[ParseMode] = ParseMode.HTML,
                              reply_message: Optional[bool] = False) -> None:
        """
        Helper function to edit or reply the message sent by bot with some text and reply_markup.

        Parameters:
            update (:class:`Update`): Update passed from the caller function.
            context (:class:`CallbackContext`): Context passed from the caller function.
            text (:obj:`str`): Text displayed in the message.
            reply_markup (:class:`ReplyMarkup`): Optional. Reply markup with the message if any. Defaults to None.
            parse_mode (:class:`ParseMode`): Optional. Parse mode to display the message with. Defaults to HTML.
            reply_message (:obj:`bool`): Optional. Whether to reply or edit the message. Defaults to edit message.

        Returns:
            (:obj:`None`)

        Notes:
            Some messages can only be replied to and not edited. `reply_message` will be automatically\
                overriden in such cases.

        Example:
            >>> def some_callback(self, update: Update, context: CallbackContext) -> USERSTATE:
                    ...
                    bot.edit_or_reply_message(
                        update=update, context=context,
                        text="some text to display",
                        reply_markup=InlineKeyboardMarkup(
                            [...]),
                        parse_mode=ParseMode.HTML.
                        reply_message=True

                    )
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
                        choices_per_row: Optional[int] = None) -> str:
        """
        In-built function to create a stage that presents the user with a series of choices.

        stage_id of the stage created is of the format {`choose:CHOICE_LABEL`}.

        Parameters:
            choice_label (:obj:`str`): The choice label of the decision to be made by user (for example: participate_in_something).
            choice_text (:obj:`str`): The text displayed when prompting user to choose.
            choices (:class:`List[Dict[str, str]`): The list of the choices to choose from.
            choices_per_row (:obj:`int`): Optional. How many choices to have in a row. Defaults to None.

        Returns:
            (:obj:`str`): Returns the unique identifier of the stage created.

        Notes:
            If `choices_per_row` is `None`, then all choices will be displayed in a single row.

        Example:
            >>> def print_fav_fruit(fruit: str, update: Update, context: CallbackContext) -> USERSTATE:
                    print(f"Your favorite fruit is: {fruit}")
                    ...

            >>> stage_id: str = bot.let_user_choose(
                    choice_label="favorite_fruit",
                    choice_text="Choose your favorite fruit",
                    choices=[
                        {
                            "text": "Apple",
                            "callback": lambda update, context: print_fav_fruit("Apple", update, context)
                        },
                        {
                            "text": "Pear",
                            "callback": lambda update, context: print_fav_fruit("Pear", update, context)
                        },
                    ],
                    choices_per_row=1
                )
                print(stage_id)  # --> "choose:favorite_fruit"
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
                            exitable: Optional[bool] = False) -> str:
        """
        In-built function to create a stage that collects a user input.

        stage_id of the stage created is of the format {`input:INPUT_LABEL`}

        Parameters:
            input_label (:obj:`str`): Label of the input sent by user (for example: answer).
            input_text (:obj:`str`): The text displayed before prompting user to enter their input.
            input_handler (:class:`Callable`): The callback function called with the user input.
            exitable (:obj:`bool`): Optional. Whether to allow users to abort input by sending "/cancel". Defaults to False.

        Returns:
            (:obj:`str`): Returns the unique identifier of the stage created.

        Example:
            >>> def print_fav_fruit(input_text: str, update: Update, context: CallbackContext) -> USERSTATE:
                    print(f"Your favorite fruit is: {input_text}")
                    ...

            >>> stage_id: str = bot.get_input_from_user(
                    input_label="favorite_fruit",
                    input_text="What is your favorite fruit?",
                    input_handler=print_fav_fruit,
                    exitable=True
                )
                print(stage_id)  # --> "input:favorite_fruit"
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
                           input_formatter: Optional[Callable] = lambda _: _,
                           additional_text: Optional[str] = "",
                           use_last_saved: Optional[bool] = True, allow_update: Optional[bool] = True) -> str:
        """
        In-built function to create a stage that collects a user info (`str`).

        stage_id of the stage created is of the format {`collect:DATA_LABEL`}

        Parameters:
            data_label (:obj:`str`): The info label of the data collected from user (from example: name).
            next_stage_id (:obj:`str`): Unique identifier of the stage to proceed to after successfully completing this stage.
            input_formatter (:class:`Callable`): Optional. A callback function used to format the input given.\
                Defaults to an empty callback.
            additional_text (:obj:`str`): Optional. Additional text to display when prompting user for info. \
                Defaults to empty string.
            use_last_saved (:obj:`bool`): Optional. Whether to consider previously set value for the info. \
                Defaults to True.
            allow_update (:obj:`bool`): Optional. Whether to allow users to update this info once set. \
                Defaults to True.

        Returns:
            (:obj:`str`): Returns the unique identifier of the stage created.

        Notes:
            If `use_last_saved` is `True`, then users are given the choice whether to use their previously saved input\
                or enter a new value.

            If `use_last_saved` is `False`, then users are always forced to enter a new value everytime they enter\
                a new conversation.

            If `allow_update` is `False`, then the first input confirmed by users will be the value used forever. \
                Users will not be given a chance to update even when entering a new conversation.

            Expected callback format for `input_formatter`:

                >>> def input_formatter(input : Union[str, bool]):
                        if str is True:
                            return "EXPECTED INPUT FORMAT"
                        else:
                            return check_input_format(inputs)


        Example:
            >>> def format_email_input(input_str: Union[str, bool]):
                    if input_str is True:
                        return "example@domain.com"
                    else:
                        input_str = utils.format_input_str(input_str, True, "@.")
                        return utils.check_if_valid_email_format(input_str)

            >>> stage_id: str = bot.get_info_from_user(
                    data_label="email",
                    next_stage_id="...",
                    input_formatter=format_email_input,
                    additional_text="We will not share your name with any external parties.",
                    use_last_saved=True,
                    allow_update=True
                )
                print(stage_id)  # --> "collect:email"
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

    def make_end_stage(self,
                       stage_id: Optional[str] = "end",
                       final_callback: Optional[Callable] = lambda *_: _,
                       goodbye_message: Optional[str] = "",
                       reply_message: Optional[bool] = True) -> str:
        """
        Creates and sets the end stage for the bot.

        Parameters:
            stage_id (:obj:`str`): Optional. Stage identifier of the end stage. Defaults to "end".
            final_callback (:class:`Callable`): Optional. A callback function called right before terminating \
                conversation. Defaults to an empty callback.
            goodbye_message(:obj:`str`): Optional. Message to display when user reaches end of conversation. \
                Defaults to empty string.
            reply_message(:obj:`bool`): Optional. Whether the goodbye_message (if any) should edit current message\
                or as a new message.

        Returns:
            (:obj:`str`): Returns the unique identifier of the stage created.

        Example:
            >>> stage_id: str = bot.make_end_stage(
                    stage_id="end",
                    goodbye_message="You have exited the conversation. \n\nUse /start to begin a new one.",
                    reply_message=True
                )
                print(stage_id)  # --> "end"
        """

        stage = EndConversation(
            stage_id=stage_id,
            next_stage_id=None,
            bot=self
        )
        stage.setup(
            final_callback=final_callback,
            goodbye_message=goodbye_message,
            reply_message=reply_message
        )

        self.end_stage = stage

        return stage_id

    def set_first_stage(self, stage_id: str) -> None:
        """
        Sets the starting stage for the bot (stage to proceed right after User sends the / start command).

        Parameters:
            stage_id (:obj:`str`): Stage identifier of the starting stage.

        Returns:
            (:obj:`None`)

        Example:
            >>> bot.set_first_stage(
                    stage_id="...",
                )
        """

        first_stage: Stage = self.get_stage_from_id(stage_id)
        assert first_stage, f"{stage_id} is not a valid/registered stage of bot"
        self.first_stage: Stage = first_stage

    def conversation_entry(self, update: Update, context: CallbackContext) -> USERSTATE:
        if update.message:
            chatid = str(update.message.chat_id)

            cached_user: User = context.user_data.get("user")
            user: User = cached_user or self.user_manager.new(chatid)

            if user:
                context.user_data.clear()
                context.user_data.update({"user": user})

                return self.proceed_next_stage(
                    current_stage_id="start",
                    next_stage_id=self.first_stage.stage_id,
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

    def start(self, live_mode: Optional[bool] = False) -> None:
        """
        Starts the bot.

        Parameters:
            live_mode (:obj:`bool`): Whether to `drop_pending_updates` when starting to poll. Defaults to False.

        Returns:
            (:obj:`None`)

        Example:
            >>> bot.start(live_mode=True)
        """

        for stage_id, registered_stage in self.stages.items():
            assert hasattr(registered_stage,
                           "users_data_initialized"), f"Stage:{stage_id} has not "\
                "initialized its users_data.\n\n"\
                "If this stage has no users_data to initialize, please set its init_users_data method to be:\n\n"\
                "def init_users_data(self) -> None:\n"\
                "\treturn super().init_users_data()"

        conversation_states = {}
        for idx, state in enumerate(self.states):
            conversation_states.update({idx: state["callbacks"]})

        start_command = CommandHandler(
            "start", self.conversation_entry)
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

    def init(self, token: str, logger: Log, config: Dict[str, Any]) -> None:
        """
        Initializes the Bot class.

        Parameters:
            token (:obj:`str`): Telegram Bot API token string.
            logger (:class:`Log`): Logger object to use for logging purposes of the bot.
            config (:class:`Dict[str, Any]`): Configurations values loaded from `config.yaml`.

        Returns:
            (:obj:`None`)

        Notes:
            This method replaces the `dunder` method `__init__` as Bot is meant to be used a `singleton`.

            Ensure that this method is only called `once` to avoid any issues.


        Example:
            >>> logger : Log = Log(...)
                config : Dict[str, Any] = utils.load_yaml_file(os.path.join("config.yaml"))
                bot.init(
                    token="...",
                    logger=logger,
                    config=config
                )
        """

        self.logger = logger
        self.token = token

        updater = Updater(token)
        dispatcher = updater.dispatcher

        self.stages: Dict[str, Stage] = {}
        self.states: List[Dict] = []

        self.first_stage: Stage = None
        self.end_stage: EndConversation = None

        self.updater = updater
        self.dispatcher = dispatcher

        self.user_manager = UserManager()

        self.config = config
        self.bot_config: Dict[str, Any] = config["BOT"]
        self.admin_chatids: List[str] = config.get("ADMIN_CHATIDS", [])
        self.anonymous_user_passcodes: bool = config.get(
            "MAKE_ANONYMOUS", False)
        self.user_passcodes: List[str] = config.get("USER_PASSCODES", [])

        self.behavior_remove_inline_markup = self.bot_config["REMOVE_INLINE_KEYBOARD_MARKUP"]

        answer_query = telegram.CallbackQuery.answer

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
                                if keep_message == "":
                                    query.message.delete()
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
