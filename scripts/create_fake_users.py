import sys
sys.path.append("src")

import os
import logging
import random
import shutil
import datetime
import argparse
import string
from typing import List

from bot import Bot
from user import User, UserManager
from stages.ctf import Ctf
from utils.log import Log
from utils import utils

import reset_project

MAX_ATTEMPTS = 3

MAX_NUMBER_OF_USERS = len(string.ascii_uppercase)
FAKE_GROUPS = ["Alpha", "Beta", "Charlie"]
TEMP_LOG_FILE = os.path.join("logs", "create_fake_users.log")


# 2022-05-20 13:13:11,681 [INFO] $CODE::CREATING_NEW_USER || User:0 is a new user. Creating their files...
# 2022-05-20 13:16:03,170 [INFO] $CODE::USER_CTF_VIEW_HINT_0_0 || User:0 has revealed hint 0 for Challenge 0
# 2022-05-20 13:16:04,564 [INFO] $CODE::USER_CTF_VIEW_HINT_0_1 || User:0 has revealed hint 1 for Challenge 0
# 2022-05-20 13:16:08,290 [INFO] $CODE::USER_CTF_WRONG_ANSWER_0 || User:0 @INPUT_ANSWER@ got the answer WRONG for Challenge 0
# 2022-05-20 13:16:13,570 [INFO] $CODE::USER_CTF_CORRECT_ANSWER_0 || User:0 @TOTAL_SCORE@ got the answer CORRECT for Challenge 0


users_directory = os.path.join("users")
banned_users_yaml_file = os.path.join(users_directory, "banned_users.yaml")

banned_chatids = utils.load_yaml_file(banned_users_yaml_file) or []
chatids = [chatid for chatid in os.listdir(
    users_directory) if os.path.isdir(os.path.join(users_directory, chatid))]


def override_init(self, logger: Log) -> None:
    self.logger = logger

    self.stages = {}
    self.states = []

    self.user_manager = UserManager()


Bot.init = override_init


class Emulator:
    def __init__(self, names: List[str]):
        self.logger: Log = Log(
            name=__name__,
            log_level=logging.DEBUG,
            file_handle=TEMP_LOG_FILE
        )

        self.bot: Bot = Bot()
        self.bot.init(self.logger)

        self.user_manager: UserManager = UserManager()
        self.user_manager.init(
            logger=self.logger,
            log_user_logs_to_app_logs=False)

        self.ctf: Ctf = Ctf(
            stage_id="ctf",
            next_stage_id="",
            bot=self.bot
        )
        self.ctf.setup()
        self.challenges = self.ctf.challenges

        self.fake_users = {}
        self.fake_time = {}

        for name in names:
            chatid = name  # self.generate_chatid()
            user: User = self.user_manager.new_user(chatid)

            user.update_user_data("name", name)
            user.update_user_data("username", name)
            user.update_user_data(
                "group", FAKE_GROUPS[random.randint(0, len(FAKE_GROUPS)) - 1])

            self.fake_users.update({name: user})
            self.fake_time.update({name: datetime.datetime.now()})

            with open(user.log_file, 'w', encoding="utf-8") as log_file:
                time = self.fast_forward_time(name, 5)
                log_file.write(
                    f"{time} [INFO] $CODE::CREATING_NEW_USER || User:{chatid} is a new user. Creating their files...\n")

        self.logger.quit()
        os.remove(TEMP_LOG_FILE)

    def create_log_line(self, name: str, time: str, log: str) -> None:
        fake_user: User = self.fake_users.get(name)
        with open(fake_user.log_file, 'a', encoding="utf-8") as log_file:
            log_file.write(f"{time} {log}" + "\n")

    def set_score(self, name: str, score: int) -> None:
        fake_user: User = self.fake_users.get(name)
        fake_user.data.get("ctf_state").update({"total_score": score})
        fake_user.save_user_to_file()

    def add_score(self, name: str, score: int) -> int:
        fake_user: User = self.fake_users.get(name)
        fake_user.data.get("ctf_state").update(
            {"total_score": fake_user.data.get(
                "ctf_state").get("total_score") + score}
        )
        fake_user.save_user_to_file()

        return fake_user.data.get("ctf_state").get("total_score")

    def attempt_challenge(self, name: str, challenge_number: int) -> None:
        fake_user: User = self.fake_users.get(name)

        chatid = fake_user.chatid

        self.create_log_line(
            name,
            self.fast_forward_time(name, multiplier=6),
            f"[INFO] $CODE::USER_CTF_WRONG_ANSWER_{challenge_number} "
            f"|| User:{chatid} @flag@ got the answer WRONG for Challenge {challenge_number}")

    def complete_challenge(self, name: str, challenge_number: int) -> None:
        fake_user: User = self.fake_users.get(name)

        chatid = fake_user.chatid
        ctf_state = fake_user.data.get("ctf_state")

        challenge_info = ctf_state.get("challenges")[challenge_number]
        challenge_score = challenge_info["points"]
        total_deductions = challenge_info["total_hints_deduction"]

        current_total_score = self.add_score(
            name, challenge_score - total_deductions)
        self.create_log_line(
            name,
            self.fast_forward_time(name, multiplier=7),

            f"[INFO] $CODE::USER_CTF_CORRECT_ANSWER_{challenge_number} "
            f"|| User:{chatid} @{current_total_score}@ got the answer CORRECT for Challenge {challenge_number}")

    def view_hint(self, name: str, challenge_number: int, hint_number: int) -> None:
        fake_user: User = self.fake_users.get(name)

        chatid = fake_user.chatid
        ctf_state = fake_user.data.get("ctf_state")

        challenge_info = ctf_state.get("challenges")[challenge_number]
        challenge_score = challenge_info["points"]
        hint_deduction = challenge_info["hints"][hint_number]["deduction"]
        challenge_info["total_hints_deduction"] += hint_deduction

        fake_user.save_user_to_file()
        self.create_log_line(
            name,
            self.fast_forward_time(name, multiplier=3),

            f"[INFO] $CODE::USER_CTF_VIEW_HINT_{challenge_number}_{hint_number} "
            f"|| User:{chatid} has revealed hint {hint_number} for Challenge {challenge_number}")

    def fast_forward_time(self, name: str, multiplier: int = 5) -> str:
        random_minutes = (random.random() + 0.2) * 5
        self.fake_time.update(
            {name: self.fake_time.get(name) +
                datetime.timedelta(minutes=random_minutes)
             }
        )
        return self.fake_time.get(name).strftime("%Y-%m-%d %H:%M:%S,%f")

    def generate_chatid(self) -> str:
        chatid = str(random.randint(100, 1000))
        if chatid in chatids or chatid in banned_chatids:
            return self.generate_chatid()
        else:
            chatids.append(chatid)
            return chatid

    def run(self, min_challenges_attempted: int = 5) -> None:
        total_no_of_challenges = len(self.challenges)
        for name, user in self.fake_users.items():
            user: User = user

            challenges_to_consider = random.randint(
                min(min_challenges_attempted, total_no_of_challenges), total_no_of_challenges)

            attempted_challenges = []

            print(f"{name} will be attempting {challenges_to_consider} challenges")
            for _ in range(0, challenges_to_consider):
                challenge_number = random.randint(1, total_no_of_challenges)

                while challenge_number in attempted_challenges:
                    challenge_number = random.randint(
                        1, total_no_of_challenges)

                attempted_challenges.append(challenge_number)
                challenge_number -= 1
                challenge_data: List = self.challenges[challenge_number]
                total_possible_hints = len(challenge_data["hints"])

                hints_to_use = random.randint(0, total_possible_hints)
                hints_used = []

                for _ in range(0, hints_to_use):
                    hint_number = random.randint(1, hints_to_use)

                    while hint_number in hints_used:
                        hint_number = random.randint(1, hints_to_use)

                    hint_number -= 1
                    hints_used.append(hint_number)
                    # print(f"{name} has view hint {hint_number} for challenge {challenge_number}")
                    self.view_hint(name, challenge_number, hint_number)

                to_complete = random.random()
                if to_complete > 0.4:
                    number_of_attempts = random.randint(0, MAX_ATTEMPTS)
                    for _ in range(0, number_of_attempts):
                        self.attempt_challenge(name, challenge_number)
                    # print(f"{name} has completed challenge {challenge_number}")
                    self.complete_challenge(name, challenge_number)
                else:
                    # print(f"{name} has attempted challenge {challenge_number}")
                    self.attempt_challenge(name, challenge_number)


def main(number_of_users: int = 26, min_challenges_attempted: int = 5) -> None:
    reset_project.reset_project(log_file=TEMP_LOG_FILE)

    print(
        f"Creating {number_of_users} users with a minimum of {min_challenges_attempted} challenge attempts")
    fake_names = [f"PERSON {char}" for char in string.ascii_uppercase[:min(
        number_of_users, MAX_NUMBER_OF_USERS)]]
    emulator: Emulator = Emulator(fake_names)
    emulator.run(min_challenges_attempted)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()

    PARSER.add_argument(
        "-n", type=int, help="Number of users to generate. Max is 26. If set to 0 then max will be taken.", default=0, required=False)
    PARSER.add_argument(
        "-c", type=int, help="Number of challenges to attempt per user.", default=5, required=False)

    ARGS = PARSER.parse_args()

    main(ARGS.n or MAX_NUMBER_OF_USERS, ARGS.c)
