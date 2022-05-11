import os
import random
import string
import argparse

from datetime import datetime

stages_folder = os.path.join("src", "stages")


def strip_string_constructors(s: str) -> str:
    return ''.join([char for char in s if char not in '",'])


def generate_passcodes(new_users: list) -> None:
    config_yaml_file = os.path.join(os.getcwd(), "config.yaml")

    assert os.path.isfile(config_yaml_file), "authenticate.py not found"

    raw_data = {}
    with open(config_yaml_file, 'r') as stream:
        raw_data = stream.readlines()

    start_marker_idx, end_marker_idx = False, False
    for idx, line in enumerate(raw_data):
        if "# START_PASSCODES_MARKER" in line:
            start_marker_idx = idx
        elif "# END_PASSCODES_MARKER" in line:
            end_marker_idx = idx
            break

    assert start_marker_idx is not False, "START marker missing from config.yaml->USER_PASSCODES"
    assert end_marker_idx is not False, "END marker missing from config.yaml->USER_PASSCODES"

    current_passcodes = {}
    new_passcodes = {}

    for idx in range(start_marker_idx + 1, end_marker_idx - 1):
        line = raw_data[idx]
        line = ''.join(char for char in line if (
            char != '#' and char != ' ' and char != '\n'))
        marker = line.find(':')

        if marker > 0:
            passcode = strip_string_constructors(line[:marker])
            registered_user = strip_string_constructors(line[marker+1:])
            current_passcodes.update({passcode: registered_user})

    for user_info in new_users:
        user, group = None, None
        if type(user_info) is list:
            user, group = user_info
        else:
            user, group = user_info, "none"

        random_passcode = ""

        while random_passcode == "" or random_passcode in current_passcodes:
            # string.ascii_uppercase - (I, L, O, U, V)
            possible_letters = "ABCDEFGHJKMNPQRSTWXYZ"
            letter = random.choices(possible_letters, k=1)
            numbers = random.choices(string.digits, k=4)
            numbers[:] = [str(x) for x in numbers]

            random_passcode = ''.join(letter) + ''.join(numbers)

        current_passcodes.update({user: random_passcode})
        new_passcodes.update({user: [random_passcode, group]})

    raw_data.insert(end_marker_idx, "  #------\n\n")
    for user, info in new_passcodes.items():
        new_passcode, group = info
        raw_data.insert(
            end_marker_idx, f"""  {new_passcode}:\n    - {user}\n    - {group}\n\n""")
    raw_data.insert(
        end_marker_idx, "  # Refer to src.runtime.generate_passcodes for more details.\n\n")
    raw_data.insert(
        end_marker_idx, f"""  # Generated at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n""")
    raw_data.insert(end_marker_idx, "\n  #------\n")

    with open(config_yaml_file, 'w') as config_file:
        config_file.writelines(raw_data)


def get_new_users_from_file(file_name: str) -> list:
    file = os.path.join(os.getcwd(), file_name)

    assert os.path.isfile(
        file), "THE INPUT FILE IS NOT FOUND. Please ensure that it is spelt correctly and is found in the root directory of the project."
    new_users = []
    with open(file, "r") as stream:
        lines = list((line.rstrip() for line in stream.readlines()))
        for line in lines:
            name, group = None, None
            if line.find(',') > 0:
                name, group = line.split(',')
                group = group.strip()
            else:
                name, group = line, "none"
            new_users.append([name, group])

    return new_users


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "-i", type=str, help="Input file with users list.", default=None, required=False)
    ARGS = PARSER.parse_args()

    generate_passcodes(
        get_new_users_from_file(ARGS.i) if ARGS.i else [
            ["guest0", "guest"],
            "guest1"
        ]
    )
