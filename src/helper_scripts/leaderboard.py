import sys
sys.path.append("src")

import os
import time
import json
import argparse
from typing import (List, Dict, Union)

from utils.utils import load_yaml_file
from stages.ctf import MAX_LEADERBOARD_VIEW
from stages.guardian import TEAMS_DESC

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
                userdata = load_yaml_file(user_yaml_file)

                if userdata:
                    ctf_state = userdata.get("ctf_state")
                    guardian_state = userdata.get("guardian_state", {})

                    if ctf_state:
                        user_total_score = str(ctf_state["total_score"])

                        if int(user_total_score) > -1:
                            if user_total_score not in scoring_dict:
                                scoring_dict.update({user_total_score: []})

                            # In our curent version, we use username for display on leaderboard
                            # instead of name, do change this according to your format
                            # user_name = userdata.get("name")
                            user_name = userdata.get("username")

                            # Old userdata we used to collect
                            # user_phonenumber = userdata.get("phone number")
                            # user_email = userdata.get("email")

                            # Teams is a userdata used by stage:guardian
                            user_teams = guardian_state.get("teams", [])
                            user_teams = user_teams if len(
                                user_teams) > 0 else guardian_state.get("teams.history")

                            if user_teams:
                                for idx, team in enumerate(user_teams):
                                    user_teams[idx] = TEAMS_DESC.get(
                                        team, "no_team_found")
                            else:
                                user_teams = []

                            if user_name:
                                scoring_dict[user_total_score].append(
                                    {
                                        "name": user_name,
                                        # "phone number": user_phonenumber if user_phonenumber else "no_phonenumber_found",
                                        # "email": user_email if user_email else "no_email_found",
                                        "teams": '+'.join(user_teams if len(user_teams) > 0 else ["no_team_found"]),
                                        "chatid": chatid,
                                        "last_score_update": ctf_state.get("last_score_update")
                                    }
                                )

    for total_score, users in scoring_dict.items():
        users.sort(key=lambda a: a["last_score_update"])
        scoring_list.append([int(total_score), users])
    scoring_list.sort(reverse=True, key=lambda a: a[0])

    row, col, count, stopped = 0, 0, 0, False

    for p in scoring_list:
        col = 0
        for u in p[1]:
            count += 1
            if count > min(MAX_LEADERBOARD_VIEW, max_leaderboard_view):
                stopped = True
                break
            col += 1

        if stopped:
            break
        else:
            row += 1

    scoring_list[row][1] = scoring_list[row][1][:col]
    scoring_list = scoring_list[:row + 1]

    return scoring_list

    # scoring_list
    [
        # [points, users]
        [0, [
            {
                "name": "",
                # "phone number": "",
                # "email": "",
                "teams": "",
                "chatid": "",
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

    lines_to_write.append(
        # "Score,Name,Phone Number,Email,Guardian Team\n"
        "Score,Name,Guardian Team, ChatID\n"
    )

    for placing_array in scoring_list:
        total_score, top_users = placing_array

        for user in top_users:
            line = (f"""{total_score},"""
                    f"""{user["name"]},"""
                    f"""{user["teams"]},"""
                    f"""{user["chatid"]}\n""")
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
