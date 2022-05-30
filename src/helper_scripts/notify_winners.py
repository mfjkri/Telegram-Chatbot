import sys
sys.path.append("src")

import os
import requests

from helper_scripts.leaderboard import update_leaderboard
from utils.utils import load_yaml_file

CONFIG = load_yaml_file(os.path.join("config.yaml"))
LIVE_MODE = CONFIG["RUNTIME"]["LIVE_MODE"]
BOT_TOKEN = CONFIG["BOT_TOKENS"]["LIVE"] if LIVE_MODE else CONFIG["BOT_TOKENS"]["TEST"]


def send_message(chatid: str, name: str, title: str, message: str) -> None:
    print(
        "Sending Request to:", chatid, name,
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chatid}&text=<b>{title}</b>\n\n{message}&parse_mode=HTML")
    )


def message_top_3() -> None:
    top_users = update_leaderboard(top_placing=3)

    placing_decorater = ["st 🥇", "nd 🥈", "rd 🥉"]

    for placing, placing_array in enumerate(top_users):
        total_score, top_users = placing_array

        for user in top_users:
            chatid = user["chatid"]  # "1026217187"
            name = user["name"]

            placing_text = f"{placing + 1}{placing_decorater[placing]}"

            send_message(
                chatid=chatid,
                name=name,
                title=f"\nCONGRATULATIONS {name.upper()}!! 🎉🎉\n\n You placed {placing_text}\n",
                message="Come down to the booth by 3pm to collect your prize.\nAny prizes not collected by end of the day will be forfeited!"
            )


def main() -> None:
    message_top_3()


if __name__ == "__main__":
    main()
