import requests

from leaderboard import update_leaderboard

LIVE_MODE = True
BOT_TOKEN = "1735980186:AAEmTPvc2APQubsF1RsDJzLt85cbNA7DV7E" if LIVE_MODE else "5099836053:AAF80IRmmVI-mgtvlYFzc_l6WVBwjNqY7hQ"


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


def main():
    message_top_3()


if __name__ == "__main__":
    main()
