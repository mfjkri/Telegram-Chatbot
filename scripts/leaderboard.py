"""
Leaderboard lines will be in the format:

SCORE, ${RELEVANT_DATA_FIELDS}, CHATID

Enter in what data fields to include below:

    for example:

        RELEVANT_DATA_FIELDS = {
            "name": ["name", str, "anonymous"],
            "group": ["group", str, "no-group"]
        }
    
    Take note that the first element in the list is the path of the data-field
    in user.data
    
    for example:
    
        "guardian_team": ["guardian_state:teams_str", str, ""]
        
        this means that the data-label guardian_team can be found at:
        
            `user.data.get("guardian_state",{}).get("teams_str", "")`
"""

RELEVANT_DATA_FIELDS = {
    # "data-field-label" : [path-in-user-data, constructor, default_value]
    "name": ["username", str, "anonymous"],
    "group": ["group", str, "no-group"],
    "guardian_team": ["guardian_state:teams_str", str, ""]
}

import sys
sys.path.append("src")

import os
import time
import json
import argparse
from typing import (List, Dict, Any, Callable, Union)

from utils.utils import load_yaml_file

users_directory = os.path.join("users")
leaderboard_export_file = os.path.join("exports", "exported_leaderboard.csv")


def update_leaderboard(max_leaderboard_view: int) -> List[List[Union[int, List[Dict[str, str]]]]]:

    scoring_dict = {}
    scoring_list = []

    for chatid in os.listdir(users_directory):
        user_directory = os.path.join(users_directory, chatid)

        if os.path.isdir(user_directory):
            user_yaml_file = os.path.join(user_directory, f"{chatid}.yaml")

            if os.path.isfile(user_yaml_file):
                user_data = load_yaml_file(user_yaml_file)

                if user_data is not None:
                    ctf_state = user_data.get("ctf_state")

                    if ctf_state:
                        user_total_score = str(ctf_state["total_score"])

                        if int(user_total_score) > -1:
                            if user_total_score not in scoring_dict:
                                scoring_dict.update({user_total_score: []})

                            extracted_data_fields = {}
                            for data_field_label, default_data_field in RELEVANT_DATA_FIELDS.items():
                                data_path: str
                                default_constructor: Callable[[*Any], Any]
                                default_value: Any

                                data_path, default_constructor, default_value = default_data_field

                                data_field_value: Union[Any,
                                                        Dict[str, Any]] = user_data

                                split_paths: List[str] = data_path.split(':')
                                for i, path in enumerate(split_paths):
                                    data_field_value = data_field_value.get(
                                        path,
                                        default_constructor(default_value) if i == len(
                                            split_paths) - 1 else {}
                                    )

                                extracted_data_fields.update(
                                    {data_field_label: str(data_field_value)})

                            scoring_dict[user_total_score].append(
                                {
                                    "name": extracted_data_fields.get("name", "name-not-valid-in-extracted-data"),
                                    "relevant_data": extracted_data_fields,
                                    "chatid": chatid,
                                    "last_score_update": ctf_state.get("last_score_update")
                                }
                            )

    for total_score, users in scoring_dict.items():
        users.sort(key=lambda a: a["last_score_update"])
        scoring_list.append([int(total_score), users])
    scoring_list.sort(reverse=True, key=lambda a: a[0])

    # row, col, count, stopped = 0, 0, 0, False

    # for p in scoring_list:
    #     col = 0
    #     for u in p[1]:
    #         count += 1
    #         if count > min(MAX_LEADERBOARD_VIEW, max_leaderboard_view):
    #             stopped = True
    #             break
    #         col += 1

    #     if stopped:
    #         break
    #     else:
    #         row += 1

    # scoring_list[row][1] = scoring_list[row][1][:col]
    # scoring_list = scoring_list[:row + 1]

    return scoring_list

    # scoring_list
    [
        # [points, users]
        [0, [
            {
                "name": "",
                "relevant_data": {},
                "chatid": "",
                "last_score_update": "",
            }
        ]],
    ]


def update_leaderboard_webpage(scoring_list: List[List[Union[int, Dict]]],
                               path_to_leaderboard_json_file: str) -> None:
    leaderboard_json = []

    for placing_array in scoring_list:
        total_score, top_users = placing_array

        for user in top_users:
            leaderboard_json.append({
                "username": user["name"] or f"""User:{user["chatid"]}""",
                "score": total_score
            })

    with open(os.path.join(path_to_leaderboard_json_file, "leaderboard.json"), 'w') as stream:
        json.dump(leaderboard_json, stream, indent=4)


def update_leaderboard_file(scoring_list: List[List[Union[int, Dict]]]) -> None:
    lines_to_write = []

    relevant_data_str = ','.join(RELEVANT_DATA_FIELDS.keys()).upper()
    lines_to_write.append(
        f"SCORE,{relevant_data_str},CHATID\n"
    )

    for placing_array in scoring_list:
        total_score, top_users = placing_array

        for user in top_users:
            relevant_data_str = ','.join(
                user["relevant_data"].values())

            line = (f"""{total_score},"""
                    + relevant_data_str
                    + f""", {user["chatid"]}\n""")
            # {user["phone number"]},\
            # {user["email"]},\

            lines_to_write.append(line)

    with open(leaderboard_export_file, "w") as file:
        file.writelines(lines_to_write)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "-n", type=int,
        help="Limit leaderboard up to a certain placing. Defaults to no limit (all users will be ranked).",
        default=0, required=False)
    PARSER.add_argument(
        "-o", type=str,
        help="Path to output the leaderboard JSON file to. Defaults to root directory: ${rootDir} / leaderboard.json",
        default="", required=False)
    PARSER.add_argument(
        "--disable_webpage_leaderboard_file", type=bool,
        help="If set to any value, the leaderboard.json file will not be generated.")
    ARGS = PARSER.parse_args()

    max_leaderboard_view = ARGS.n or len(os.listdir(users_directory)) - 2

    print("Leaderboard.py is now running... (Press CTRL + C to stop)")
    while True:
        scoring_list = update_leaderboard(max_leaderboard_view)
        update_leaderboard_file(list(scoring_list))

        if not ARGS.disable_webpage_leaderboard_file:
            update_leaderboard_webpage(list(scoring_list), ARGS.o)
        time.sleep(1)
