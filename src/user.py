import sys
import os
import copy
import logging

from types import NoneType
from typing import (List, Dict, Any, Union)

from utils import utils
from utils.log import Log

users_directory = utils.get_dir_or_create(os.path.join("users"))
banned_users_yaml_file = os.path.join(users_directory, "banned_users.yaml")


class User():
    """
    This object represents a single user in our bot.

    You can retrieve this user object either through:

        Through context (:class:`CallbackContext`):

            1) `context.user_data.get("user")` -> `Union[User, None]`

        Through user_manager (:class:`UserManager`):

            1) `user_manager.get_from_chatid(chatid)` -> `Union[User, None]`

            2) `user_manager.get_users()` -> `Dict[str, User]`

            3) `user_manager.new_user(chatid)` -> `User`

    ---

    Parameters:
        - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).
        - application_logfilehandler (:class:`logging.FileHandler`): Log file handler used by Bot.
        - user_manager (`class`:UserManager): UserManager object that created this User object.

    ---

    Attributes:
        - logger (:class:`Log`): Logging object that only this User object will use.
        - user_manager: (:class:`UserManager`): UserManager object that this User object is part of.

        - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).
        - data (:class:`Dict[str, Any]`): Dict of userdata, typically data is bundled into states.
        - is_banned: (:obj:`bool`): Whether the User is a banned user.

        - answered_callback_queries: (:class:`List[str]`): List of CallbackQuery that have been answered.

        - directory (:obj:`str`): Path to User files in the users directory.
        - log_file (:obj:`str`): Path to log file in the User directory.
        - yaml_file (:obj:`str`): Path to data file in the User directory.

    """

    def __init__(self, chatid: str,
                 application_logfilehandler: logging.FileHandler,
                 user_manager):
        self.logger = Log(
            name=f"user:{chatid}",
            stream_handle=sys.stdout,
            log_level=logging.INFO
        )
        self.user_manager = user_manager

        self.chatid = chatid
        self.data: Dict[str, Any] = {}
        self.is_banned = False

        self.answered_callback_queries: List[str] = []

        self.directory = os.path.join(users_directory, chatid)
        user_exists = os.path.isdir(self.directory)
        self.directory = utils.get_dir_or_create(self.directory)

        self.log_file = os.path.join(self.directory, f"{self.chatid}.log")
        self.logger.add_filehandle(self.log_file)

        if user_exists:
            self.yaml_file = self.__load_from_file()
        else:
            self.yaml_file = self.__set_to_default_user_data()

        self.save_to_file()
        if user_manager.log_user_logs_to_app_logs:
            self.logger.add_filehandler(application_logfilehandler)

    def __set_to_default_user_data(self) -> None:
        """
        Internal private function to set its user data to default values.

        ---

        Parameters:
            - None

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            It is better to call @User.reset_user if you wish to reset user's data as \
                it also includes saving the changes to file.
        """
        self.logger.info("CREATING_NEW_USER",
                         f"User:{self.chatid} is a new user. Creating their files...")

        user_data: Dict[str, Any] = copy.deepcopy(
            self.user_manager.data_fields)
        self.data = user_data

        return os.path.join(self.directory, f"{self.chatid}.yaml")

    def __update_user_data_from_file(self, user_data: Dict[str, Any]) -> Dict:
        # TODO Update outdated user data with new data fields (user_manager.data_fields)
        return user_data

    def __load_from_file(self) -> None:
        """
        Internal private function to load user from file.

        This function will read existing user/[chatid]/[chatid].yaml file and load its content \
            into user.data if successful.

        ---

        Parameters:
            - None

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            If loading of data was unsuccessful either due to file missing or unable to read file \
                format, then user data will be set to default values (@User.set_to_default_user_data).
        """

        self.logger.info(False, "\n")
        self.logger.info(
            "NEW_SESSION", f"User:{self.chatid} is starting a new session and resuming their progress...")

        user_yaml_file = os.path.join(self.directory, f"{self.chatid}.yaml")
        user_yaml_file_exists = os.path.isfile(user_yaml_file)

        user_data = utils.load_yaml_file(
            user_yaml_file, self.logger) if user_yaml_file_exists else None

        if user_yaml_file_exists and user_data is not None:
            # Update their saved data in case of format changes
            self.data = self.__update_user_data_from_file(user_data)
            self.logger.info("LOADED_USER_FROM_FILE",
                             f"Loaded User:{self.chatid} from file.")

            return user_yaml_file
        else:
            if not user_yaml_file_exists:
                self.logger.error(
                    "USERDATA_MISSING", f"User:{self.chatid} userdata is missing. Creating a new one...")
            else:
                self.logger.error(
                    "USERDATA_CORRUPTED", f"User:{self.chatid} userdata is corrupted! Resetting his/her state...")

            # Create new user since their old data could not be found / loaded
            return self.__set_to_default_user_data()

    def save_to_file(self) -> None:
        """
        Helper function to save user to file.

        This function will dump User.data into its yaml file: users/[chatid]/[chatid].yaml

        ---

        Parameters:
            - None

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            Currently if data fails to be saved to file, only an error message is shown.

            It will not retry to save the user's data.

        ---

        Example:
            >>> user: User = ....
                # modify user.data here
                user.save_to_file()
        """

        if not utils.dump_to_yaml_file(
                self.data, self.yaml_file, self.logger):
            self.logger.error("USERDATA_FAILED_TO_SAVE",
                              f"User:{self.chatid} userdata has failed to be saved. Trying again later...")

    def update_user_data(self, data_label: str, data_value: Any) -> None:
        """
        Helper function to modify user data.

        This function will also save changes to file for you.

        ---

        Parameters:
            - data_label (:obj:`str`): Key that points to the value being updated to user data.
            - data_value (:class:`Any`): The new value.

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            This method should only be used to modify changes that are directly under `user.data`:

            For example:

                >>> user.data = {
                        "name": "",
                        "group": "",
                        #
                        "ctf_state": {
                            ...,
                            "total_score" = 10
                        }
                    }

                1) In this example, only `name` and `group` should be modified using this method.

                    >>> user.update_user_data(
                            data_label="name",
                            data_value="MyNameIsBob"
                        )

                2) Modify `total_score` by changing its value directly:
                    >>> user.data["ctf_state"]["total_score"] = NEW_VALUE
                        # OR
                        user.data["ctf_state"].update({
                            "total_score":NEW_VALUE
                        })
                        #
                        # Don't forget to save changes to file
                        # This is so as modifying it manually like this won't automatically
                        # save the changes to file.
                        user.save_to_file()

                3) `ctf_state` can be modified using this method if you are updating its entire value:

                    >>> user.update_user_data(
                            data_label="ctf_state",
                            data_value={
                                ...,
                                "total_score" = NEW_VALUE
                            }
                        )

        ---

        Example:
            Refer to Notes section above.
        """

        self.data.update({data_label: data_value})
        self.save_to_file()

    def reset_user(self) -> None:
        """
        Helper function to reset user.

        This function will reset user data to default values and overwrite user files.

        ---

        Parameters:
            - None

        ---

        Returns:
            (:obj:`None`)

        ---

        Example:
            >>> user: User = ....
                user.reset_user()
        """

        self.__set_to_default_user_data()
        self.save_to_file()


class UserManager():
    """
    This object represents a Singleton class for managing User objects.

    You will primarily interface with this class when writing custom stages.

    ---

    Parameters:
        - None

        Please read the `Notes` section below.

    ---

    Notes:

        The initialization of this class has been moved from the dunder method \
            `__init__` instead to a method: `UserManager.init`.

        >>> user_manager = UserManager()
            user_manager.init(
                logger=logger,
                log_user_logs_to_app_logs=False
            )

        This is due to `UserManager` being a `Singleton` class, we would want to prevent \
            multiple initialization of the class object.

    ---

    Attributes:
        - logger (:class:`Log`): Logging object that the UserManager will use (same Logger used by Bot).
        - application_logfilehandler (:class:`logging.FileHandler`): Log file handler used by Bot.
        - log_user_logs_to_app_logs (:obj:`bool`): Whether to log user logs to application logs as well \
            (can cause too much logs if set to True).

        - users (:class:`Dict[str, User`): Dict of registered User objects where chatid is used as the key.
        - data_fields (:class:`Dict[str, Any]`):  Dict of user data that is used by registered `stages`.

        - banned_users (:class:`List[str]`):  List of chatids belonging to banned users.
    """

    def new_user(self, chatid: str) -> User:
        """
        Create a new `User` object.

        This function will a new User object with the given chatid and keep a reference to it.

        ---

        Parameters:
            - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).

        ---

        Returns:
            (:class:`User`): Returns the User object created or an existing User object with provided chatid.

        ---

        Notes:
            If a User object associated with the given chatid already exists, then it will not create \
                a new User object but instead just return the existing one.

        ---

        Example:
            >>> user_manager = UserManager()
                user_manager.init(...)
                #
                user: User = user_manager.new_user(chatid="CHATID")
        """

        # self.update_banned_list()
        if chatid not in self.users:
            self.logger.info("CREATING_USER_CLASS",
                             f"Creating UserClass for User:{chatid}.")
            user = User(chatid, self.application_logfilehandler, self)

            if chatid in self.banned_users:
                user.is_banned = True

            self.users.update({chatid: user})
            return user
        else:
            self.logger.info("USING_CACHED_USER_CLASS",
                             f"Using cached UserClass for User:{chatid}.")
            return self.users.get(chatid)

    def get_from_chatid(self, chatid: str) -> Union[User, None]:
        """
        Returns an existing User by chatid if found, else None.

        ---

        Parameters:
            - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).

        ---

        Returns:
            (:class:`User`|:obj:`None`): Returns the User object if found, else return None.

        ---

        Example:
            >>> user_manager.new_user(chatid="CHATID")
                # ...
                target_user0: Union[User, None] = user_manager.get_from_chatid(
                    chatid="CHATID")
                # target_user0 --> User
                target_user1: Union[User, None] = user_manager.get_from_chatid(
                    chatid="CHATID1")
                # target_user1 --> None
        """

        return self.users.get(chatid)

    def get_users(self) -> Dict[str, User]:
        """
        Get a Dict containing all the created users.

        Each user can be indexed using their chatid.

        ---

        Parameters:
            - None

        ---

        Returns:
            (:class:`Dict[str, User]`): Returns a Dict containing all created users, indexed with their chatid.

        ---

        Example:
            >>> user_manager.new_user(chatid="CHATID")
                user_manager.new_user(chatid="CHATID2")
                # ...
                users: Dict[str, User] = user_manager.get_users()
                #
                for chatid, user in users.items():
                    user: User
                    # ...
        """

        return self.users

    def ban_user(self, chatid: str) -> None:
        """
        Bans a User.

        This will add the user chatid to the banned_list.

        Banned users will not be able to proceed to any stages, meaning that effectively, they \
            are unable to use the Chatbot at all.

        ---

        Parameters:
            - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).

        ---

        Returns:
            (:obj:`None`)

        ---

        Example:
            >>> user_manager.new_user(chatid="CHATID")
                # ...
                user: Union[User, None] = user_manager.get_from_chatid(
                    chatid="CHATID")
                if user:
                    user_manager.ban_user(user.chatid)
        """

        self.__update_banned_list()

        user: User = self.get_from_chatid(chatid)
        if user:
            # user.reset_user()
            user.is_banned = True

        self.banned_users.append(chatid)
        utils.dump_to_yaml_file(
            self.banned_users, banned_users_yaml_file, self.logger)

    def unban_user(self, chatid: str) -> None:
        """
        Unbans a User.

        This will remove the user chatid from the banned_list.

        User will now be able to proceed to any stages, effectively allowing them to use the \
            Chatbot again.

        ---

        Parameters:
            - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            If User is currently not already banned, then nothing happens.

        ---

        Example:
            >>> user_manager.new_user(chatid="CHATID")
                user_manager.ban_user(chatid="CHATID")
                # ...
                user: Union[User, None] = user_manager.get_from_chatid(
                    chatid="CHATID")
                if user:
                    user_manager.unban_user(user.chatid)
        """

        self.__update_banned_list()

        if chatid in self.banned_users:
            self.banned_users.remove(chatid)
            utils.dump_to_yaml_file(
                self.banned_users, banned_users_yaml_file, self.logger)
            self.__update_banned_list()

            user: User = self.get_from_chatid(chatid)
            if user:
                user.is_banned = False

    def __update_banned_list(self) -> None:
        """
        Internal private function to update banned list.

        Reads and writes to file users/banned_users.yaml.

        ---

        Parameters:
            - None

        ---

        Returns:
            (:obj:`None`)
        """

        banned_users = utils.load_yaml_file(
            banned_users_yaml_file, self.logger) if os.path.isfile(banned_users_yaml_file) else False
        if not isinstance(banned_users, Union[NoneType, bool]):
            if not banned_users:
                assert True, "hello"
            self.banned_users = banned_users

            for chatid in banned_users:
                user: User = self.get_from_chatid(chatid)
                if user:
                    user.is_banned = True
        else:
            self.logger.warning("BAN_LIST_CORRUPTED_OR_MISSING",
                                "Creating and overwriting to an empty list.")
            self.banned_users = []
            utils.dump_to_yaml_file(
                self.banned_users, banned_users_yaml_file, self.logger)

    def add_data_field(self, data_label: str, value: Any):
        """
        Adds a data field to User.data which a given default value.

        This data field will be initialized everytime a new User is created or resetted.

        ---

        Parameters:
            - data_label (:obj:`str`): Key that points to the value being added to user data.
            - value (:class:`Any`): The value that the data_label points to in user data.

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            This function is generally called within a Stage (@init_users_data).

            Stages that require multiple user attributes, should bundle them all into a single state Dict.

            >>> # In src/stages/SomeStage.py
                class SomeStage(Stage):
                    def init_users_data(self) -> None:
                        stage_state = {
                            "some_attribute": 0,
                            "another_attribute": "",
                            "example_list": []
                        }
                        #
                        self.user_manager.add_data_field(
                            "stage_state", stage_state)

            You can retrieve the initialized data later in `User.data`:

            >>> class SomeStage(Stage):
                    def some_handler_callback(self, update: Update, context: CallbackContext) -> USERSTATE:
                        user: User = context.user_data.get("user")
                        #
                        stage_stage = user.data.get("stage_state")
                        print(stage_stage)
                        print(stage_stage["some_attribute"])

        ---

        Example:
            Refer to Notes section.
        """

        self.data_fields.update({data_label: copy.deepcopy(value)})

    def load_users_from_file(self):
        """
        Loads all existing users from files.

        It will create a `User` object for each existing user retrieved from files.

        ---

        Parameters:
            - chatid (:obj:`str`): Unique chatid of the user account (in relation to the bot).

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            Existing users are retrieved from the users directory: `users/`

            If part of the user files are missing or corrupted (incorrected format etc), \
                then it will overwrite and load the default values for them.

            This function should not be called anywhere else but in `@Bot.start`.
        """

        for chatid in os.listdir(users_directory):
            if os.path.isdir(os.path.join(users_directory, chatid)):
                self.new_user(chatid)

    def init(self, logger: Log, log_user_logs_to_app_logs: bool = False) -> None:
        """
        Initializes the UserManager class.

        ---

        Parameters:
            - logger (:class:`Log`): Logger object to use for logging purposes of the bot.
            - log_user_logs_to_app_logs (:obj:`bool`): Whether to log user logs to application logs \
            as well (can cause too much logs if set to True).

        ---

        Returns:
            (:obj:`None`)

        ---

        Notes:
            This method replaces the `dunder` method `__init__` as UserManager is meant to be used a `Singleton`.

            Ensure that this method is only called `once` to prevent re-initialization.

        ---

        Example:
            >>> logger : Log = Log(...)
                config : Dict[str, Any] = utils.load_yaml_file(
                    os.path.join("config.yaml"))
                # ...
                user_manager = UserManager()
                user_manager.init(
                    logger=logger,
                    log_user_logs_to_app_logs=("LOG_USER_TO_APP_LOGS" in config
                                   and config["LOG_USER_TO_APP_LOGS"]))
                )
        """

        self.log_user_logs_to_app_logs: bool = log_user_logs_to_app_logs
        self.application_logfilehandler: str = logger.file_handlers[0]
        self.logger: Log = logger

        self.data_fields: Dict[str, Any] = {}

        self.users: Dict[str, User] = {}

        self.banned_users: List[str] = []
        self.__update_banned_list()

    def __new__(cls, *_):
        if not hasattr(cls, "instance"):
            cls.instance = super(UserManager, cls).__new__(cls)
        return cls.instance
