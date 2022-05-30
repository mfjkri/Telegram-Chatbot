import sys
sys.path.append("src")

import os
import shutil
import argparse
import copy
from typing import Union

from utils import utils

CTF_DIRECTORY = os.path.join(os.getcwd(), "ctf")
CHALLENGES_DIRECTORY = os.path.join(CTF_DIRECTORY, "challenges")

NUM_TO_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
                6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
                11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen",
                15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
                19: "Nineteen", 20: "Twenty", 30: "Thirty", 40: "Forty",
                50: "Fifty", 60: "Sixty", 70: "Seventy", 80: "Eighty",
                90: "Ninety", 0: "Zero"}

DEFAULT_CHALLENGE_DATA = {
    "description": "Lorem ipsum dolor, sit amet consectetur adipisicing elit. Quaerat mollitia doloribus",
    "additional_info": None,
    "answer": "",

    "points": 50,
    "time_based": False,
    "one_try": False,
    "multiple_choices": None,

    "hints": [],

    "files": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
}


def convert_int_to_word(n) -> str:
    try:
        return NUM_TO_WORDS[n]
    except KeyError:
        try:
            return NUM_TO_WORDS[n - n % 10] + NUM_TO_WORDS[n % 10]
        except KeyError:
            return "Number out of range"


def main(challenge_yaml_file: Union[bool, str], no_of_challenges: int = 4) -> None:
    clear_current_challenges()

    template_challenge_data = utils.load_yaml_file(
        challenge_yaml_file) if challenge_yaml_file and os.path.isfile(challenge_yaml_file) else DEFAULT_CHALLENGE_DATA

    for challenge_number in range(1, no_of_challenges + 1):
        challenge_data = copy.deepcopy(template_challenge_data)
        challenge_name = convert_int_to_word(challenge_number)
        challenge_answer = f"flag@{challenge_name.lower()}"

        challenge_data.update({
            "description": f"This is Challenge {challenge_name}. {template_challenge_data['description']}",
            "answer": challenge_answer,
            "points": template_challenge_data["points"] + (challenge_number * 10),

            "flags": [
                {
                    "text": "Lorem ipsum dolor sit amet.",
                    "deduction": 10 + challenge_number * 5
                },
                {
                    "text": f"Lorem ipsum, dolor sit {challenge_answer} elit. Veniam, distinctio?",
                    "deduction": 10 + challenge_number * 5
                }
            ]

        })

        challenge_directory = utils.get_dir_or_create(os.path.join(
            CHALLENGES_DIRECTORY, f"{challenge_number}-Challenge{challenge_name}"))
        challenge_yaml_file = os.path.join(
            challenge_directory, "challenge.yaml")
        utils.dump_to_yaml_file(challenge_data, challenge_yaml_file)


def clear_current_challenges() -> None:
    for challenge_name in os.listdir(CHALLENGES_DIRECTORY):
        challenge_directory = os.path.join(
            CHALLENGES_DIRECTORY, challenge_name)
        if os.path.isdir(challenge_directory):
            shutil.rmtree(challenge_directory)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()

    PARSER.add_argument(
        "-i", type=str, help="challenge.yaml input file as template", default='', required=False)

    PARSER.add_argument(
        "-n", type=int, help="Number of challenges to generate. If omitted, defaults to 4.", default=4, required=False)

    ARGS = PARSER.parse_args()

    main(ARGS.i, ARGS.n)
