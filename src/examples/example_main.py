#!D:\repos\py\_csa\CSA_Academy_CTF_v4\bot\venv\Scripts\python.exe
import sys, logging, os
from typing import (Union)

from bot import Bot
from user import Users
import utils.utils as utils
from utils.log import Log 
from stages.example import Example

LOG_FILE = os.path.join(os.getcwd(), "logs", f"csabot.log")
BOT_TOKEN = "5292154363:AAGcDCaS0PLMNbcY6uRXYV3Coneq4H2aR34"

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