import os
import yaml

from typing import Union

users_directory = os.path.join(os.getcwd(), "users")
banned_users_file = os.path.join(users_directory, "banned_users.yaml")


def load_yaml_file(file_path: str) -> Union[bool, dict]:
    with open(file_path, 'r') as stream:
        config = {}
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError:
            config = False
        return config


def dump_to_yaml_file(data: dict, file_path: str) -> bool:
    with open(file_path, 'w') as file:
        write_status = True
        try:
            yaml.dump(data, file)
        except yaml.YAMLError as exception:
            write_status = False
        return write_status


banned_users = load_yaml_file(banned_users_file) or []

for chatid in os.listdir(users_directory):
    user_directory = os.path.join(users_directory, chatid)

    if os.path.isdir(user_directory) and chatid not in banned_users:
        banned_users.append(chatid)


dump_to_yaml_file(banned_users, banned_users_file)
