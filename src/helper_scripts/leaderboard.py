import sys
sys.path.append("src")

import os
import time

from stages.ctf import MAX_LEADERBOARD_VIEW
from stages.guardian import TEAMS_DESC
from utils.utils import load_yaml_file

users_directory = os.path.join("users")
leaderboard_export_file = os.path.join("exports", "exported_leaderboard.csv")
# os.getcwd(), "..", "Chatbot-Leaderboard", "leaderboard.txt"
leaderboard_json_file = os.path.join("leaderboard.txt")


def update_leaderboard(top_placing: int = MAX_LEADERBOARD_VIEW) -> None:
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

                            user_name = userdata.get("name")
                            user_phonenumber = userdata.get("phone number")
                            user_email = userdata.get("email")
                            user_teams = guardian_state.get("teams", [])
                            user_teams = user_teams if len(
                                user_teams) > 0 else guardian_state.get("teams.history")

                            if user_teams:
                                for idx, team in enumerate(user_teams):
                                    user_teams[idx] = TEAMS_DESC.get(
                                        team, "no_team_found")
                            else:
                                user_teams = []

                            if user_name and user_name != '':
                                scoring_dict[user_total_score].append(
                                    {
                                        "name": user_name,
                                        "phone number": user_phonenumber if (user_phonenumber and user_phonenumber != '') else "no_phonenumber_found",
                                        "email": user_email if (user_email and user_email != '') else "no_email_found",
                                        "teams": '+'.join(user_teams if len(user_teams) > 0 else ["no_team_found"]),
                                        "chatid": chatid,
                                        "last_score_update": ctf_state.get("last_score_update")
                                    }
                                )

    for total_score, users in scoring_dict.items():
        users.sort(key=lambda a: a["last_score_update"])
        scoring_list.append([int(total_score), users])
    scoring_list.sort(reverse=True, key=lambda a: a[0])

    update_leaderboard_file(list(scoring_list))
    update_leaderboard_webpage(list(scoring_list))

    # scoring_list
    [
        # [points, users]
        [0, [
            {
                "name": "",
                "phone number": "",
                "email": "",
                "teams": "",
                "chatid": "",
            }
        ]],
    ]

    return scoring_list


def update_leaderboard_webpage(leaderboard: list) -> None:
    file_lines = ["{\n"]
    idx = 0

    for placing_array in leaderboard:
        total_score, top_users = placing_array

        for user in top_users:
            if idx < MAX_LEADERBOARD_VIEW:
                if not user["name"]:
                    user["name"] = f"""User:{user["chatid"]}"""
                file_lines.append(
                    f"\"{idx}\"" + " : {" +
                    f""""username" : "{user["name"]}","score" : {total_score}""" + "},\n"
                )
                idx += 1

    file_lines[-1] = file_lines[-1][:-2] + "\n"
    file_lines.append("}")
    with open(leaderboard_json_file, 'w') as stream:
        stream.writelines(file_lines)


def update_leaderboard_file(scoring_list) -> None:
    lines_to_write = []

    lines_to_write.append("Score,Name,Phone Number,Email,Guardian Team\n")

    for idx, placing_array in enumerate(scoring_list):
        total_score, top_users = placing_array

        for user in top_users:
            line = (f"""{total_score},{user["name"]},{user["phone number"]},{user["email"]},""" +
                    f"""{user["teams"]}\n""")  # {user["chatid"]}

            lines_to_write.append(line)

    with open(leaderboard_export_file, "w") as file:
        file.writelines(lines_to_write)


if __name__ == "__main__":
    print("Leaderboard.py is now running... (Press CTRL + C to stop)")
    while True:
        update_leaderboard()
        time.sleep(1)
