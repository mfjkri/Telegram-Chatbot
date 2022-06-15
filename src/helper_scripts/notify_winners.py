import sys
sys.path.extend(["src", "."])

import requests

from main import BOT_TOKEN
from bot import MESSAGE_DIVIDER
from helper_scripts.leaderboard import update_leaderboard


def send_message(chatid: str, name: str, title: str, message: str) -> None:
    print(
        "Sending Request to:", chatid, name,
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chatid}&text=<b>{title}</b>\n\n{message}&parse_mode=HTML")
    )


def message_top_3() -> None:
    top_users = update_leaderboard(max_leaderboard_view=3)

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
                title=f"🎉 Congrats {name}!! 🎉\n\n"
                f"{MESSAGE_DIVIDER}You placed {placing_text}\n{MESSAGE_DIVIDER}",
                message="Come down to the booth by 3pm to collect your prize.\n"
                        "Any prizes not collected by end of the day will be forfeited!"
            )


def main() -> None:
    message_top_3()


if __name__ == "__main__":
    main()
