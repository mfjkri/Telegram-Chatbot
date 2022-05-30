import os
import copy
import time
import datetime
import re
import functools
import operator

from telegram import (InlineKeyboardButton,
                      InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler,
                          MessageHandler, CallbackContext, Filters)

from user import UserManager, User
from bot import (Bot, USERSTATE, MESSAGE_DIVIDER)
import utils.utils as utils

MAX_LEADERBOARD_VIEW = 10


class Ctf(object):
    def __init__(self, directory: str, bot: Bot):
        self.challenges = []
        self.directory = directory
        self.challenges_directory = os.path.join(directory, "challenges")

        self.bot: Bot = bot
        self.users_manager: UserManager = UserManager()

        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None

        self.leaderboard_active = True
        self.leaderboard = []
        # self.leaderboard_file = os.path.join(directory, "leaderboard.txt")

        bot.add_custom_stage_handler(self)
        self.load_challenges()
        self.init_users_data()

    # Internal function called within bot.start

    def init_with_users_loaded(self) -> None:
        """
        Internal function for final initialization.
        Called after users are loaded from file (before bot is started): bot.start.

        :return: None
        """
        self.update_leaderboard()

    def load_challenges(self) -> None:
        """
        Internal function to load challenges from file.
        Called during initialization of CTF handler.

        :return: None
        """
        self.challenges = []

        challenges_names = os.listdir(self.challenges_directory)
        assert functools.reduce(
            operator.and_,
            [re.search(r"[0-9]+", cn) is not None for cn in challenges_names]
        ), "Please ensure that the directory names of the challenges in ctf/challenges/"\
            " are of the format:\n\tNUMBER-ChallengeName\n\te.g. 13-Decryption"\
            "\n\nFor more info, refer to README.md -> 1.2 Adding CTF Challenges"

        challenges_names.sort(
            key=lambda a: int(re.search(r"[0-9]+", a).group(0))
        )
        for _, name in enumerate(challenges_names):
            challenge_directory = os.path.join(self.challenges_directory, name)
            challenge_yaml_file = os.path.join(
                challenge_directory, "challenge.yaml")

            if os.path.isfile(challenge_yaml_file):
                challenge_data = utils.load_yaml_file(
                    challenge_yaml_file, self.bot.logger)
                if challenge_data:
                    self.challenges.append(challenge_data)

    def init_users_data(self) -> None:
        """
        Internal function to set CTF data format in userdata.
        Called during initialization of CTF handler.

        :return: None
        """
        ctf_state = {
            "total_score": 0,
            "last_score_update": datetime.datetime.now(),
            "challenges": []
        }

        for challenge in self.challenges:
            challenge_data = copy.deepcopy(challenge)

            challenge_data.update({"attempts": 0})
            challenge_data.update({"completed": False})
            challenge_data.update({"total_hints_deduction": 0})

            if type(challenge_data["time_based"]) is int:
                challenge_data["time_based"] = {
                    "limit": int(challenge_data["time_based"]),
                    "start_time": False,
                    "end_time": False
                }
            else:
                challenge_data["time_based"] = None

            max_hints_deduction = 0
            for hint in challenge_data["hints"]:
                hint.update({"used": False})
                max_hints_deduction += hint["deduction"]

            challenge_data.update({"max_hints_deduction": max_hints_deduction})
            ctf_state["challenges"].append(challenge_data)

            # Data fields related to CTF in user.data (ctf_state)
            # "ctf_state" :
            {
                "challenges": [],  # see structure for each challenge below
                "total_score": 0,
                "last_score_update": None,
            }

            # Challenge format for users (each challenge in challenges : [])
            {
                "description": "Lorem ipsum?",
                "answer": "",
                "points": 0,
                "attempts": 0,
                "completed": False,
                "total_hints_deduction": 0,
                "max_hints_deduction": 0,
                "hints": [{"deduction": 0, "text": "Lorem ipsum", "used": False}],
                "files": ["www.link.com"],
                "one_try": True,
                "time_based": {
                    "limit": 1800,
                    "start_time": False,
                    "end_time": False,
                } or False,
                "multiple_choices": [
                    "Choice A",
                    "Choice B",
                    "choice C", ...
                ] or False
            }
        self.users_manager.add_data_field("ctf_state", ctf_state)

    def entry_ctf(self, update: Update, context: CallbackContext) -> USERSTATE:
        return self.load_menu(update, context)

    def exit_ctf(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer(keep_message="-")

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.next_stage_id,
            update=update, context=context
        )

    def setup(self, stage_id: str, next_stage_id: str = "end") -> None:
        self.stage_id = stage_id
        self.next_stage_id = next_stage_id

        menu_view_callbacks = [
            CallbackQueryHandler(
                self.view_leaderboard, pattern="^ctf_view_leaderboard$", run_async=True),
            CallbackQueryHandler(
                self.exit_ctf, pattern="^ctf_exit$", run_async=True)
        ]
        challenge_view_callbacks = [CallbackQueryHandler(
            self.load_menu, pattern="^ctf_return_to_menu$", run_async=True)]
        retry_challenge_callbacks = [CallbackQueryHandler(
            self.load_menu, pattern="^ctf_return_to_menu$", run_async=True)]

        for idx_c, challenge in enumerate(self.challenges):
            menu_view_callbacks.append(
                CallbackQueryHandler(
                    self.view_challenge, pattern=f"^ctf_menu_view_challenge_{idx_c}$", run_async=True)
            )
            challenge_view_callbacks.extend([
                CallbackQueryHandler(
                    self.submit_answer, pattern=f"^ctf_submit_answer_{idx_c}$", run_async=True),
                # CallbackQueryHandler(
                #     self.view_challenge, pattern=f"^ctf_refresh_challenge_{idx_c}$", run_async=True)
            ])
            retry_challenge_callbacks.extend([
                CallbackQueryHandler(
                    self.submit_answer, pattern=f"^ctf_submit_answer_{idx_c}$", run_async=True),
                CallbackQueryHandler(
                    self.view_challenge, pattern=f"^ctf_return_to_challenge_{idx_c}$", run_async=True)
            ])

            if challenge["multiple_choices"]:
                for idx_a, _ in enumerate(challenge["multiple_choices"]):
                    challenge_view_callbacks.append(
                        CallbackQueryHandler(
                            self.submit_choice_answer, pattern=f"^ctf_select_choice_{idx_a}:{idx_c}$", run_async=True)
                    )

            for idx_h, _ in enumerate(challenge["hints"]):
                challenge_view_callbacks.append(
                    CallbackQueryHandler(
                        self.reveal_hint, pattern=f"^ctf_view_hint_{idx_h}:{idx_c}$", run_async=True)
                )

        self.stage = self.bot.add_stage(
            stage_id=stage_id,
            entry=self.entry_ctf,
            exit=self.exit_ctf,
            states={
                "MENU": menu_view_callbacks,
                "CHALLENGE_VIEW": challenge_view_callbacks,
                "LEADERBOARD_VIEW": [CallbackQueryHandler(self.load_menu, pattern="^ctf_return_to_menu$", run_async=True)],
                "SUBMIT_CHALLENGE": [MessageHandler(Filters.all, self.handle_answer, run_async=True)],
                "CHALLENGE_SUCCESS": [CallbackQueryHandler(self.load_menu, pattern="^ctf_return_to_menu$", run_async=True)],
                "CHALLENGE_WRONG": retry_challenge_callbacks
            },
        )
        self.states = self.stage["states"]
        (
            self.MENU, self.CHALLENGE_VIEW, self.LEADERBOARD_VIEW,
            self.SUBMIT_CHALLENGE, self.CHALLENGE_SUCCESS, self.CHALLENGE_WRONG,
        ) = self.bot.unpack_states(self.states)

    def load_menu(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        user.logger.info("USER_CTF_LOAD_MENU",
                         f"User:{user.chatid} has loaded ctf menu")
        ctf_state = user.data.get("ctf_state")

        keyboard = [[]]
        all_challenges_completed = True
        challenges_to_attempt = False

        for idx, challenge in enumerate(ctf_state["challenges"]):
            if idx % 2 == 0:
                keyboard.append([])

            is_challenge_completed = challenge["completed"]
            all_challenges_completed = False if not is_challenge_completed else all_challenges_completed
            challenges_to_attempt = True if (
                not is_challenge_completed and not challenge["one_try"]) else challenges_to_attempt

            button_text = f"Challenge {idx + 1}"
            if is_challenge_completed:
                button_text += "  ✅"
            else:
                if challenge["time_based"]:
                    pass
                    # button_text += "  ⌛️"
                    # button_text += f""" ({challenge["points"]} pts)"""
                if challenge["one_try"]:
                    if challenge["attempts"] == 0:
                        challenges_to_attempt = True
                        # button_text += "  ⚠️"
                        # button_text += f""" ({challenge["points"]} pts)"""
                    else:
                        button_text += "  ❌"

            keyboard[-1].append(
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"ctf_menu_view_challenge_{idx}"
                )
            )
        if self.leaderboard_active:
            keyboard.append([InlineKeyboardButton(
                "Leaderboard 📈", callback_data="ctf_view_leaderboard")])
        keyboard.append([InlineKeyboardButton(
            "Exit 👋", callback_data="ctf_exit")])

        ctf_menu_msg = ""
        if all_challenges_completed:
            ctf_menu_msg += "🥳🎉  CONGRATULATIONS!  🎉🥳\n\n"
            ctf_menu_msg += "You have solved <b>all</b> the challenges!\n\n"
        elif not challenges_to_attempt:
            ctf_menu_msg += "🥳🎉  CONGRATULATIONS!  🎉🥳\n\n"
            ctf_menu_msg += "You have attempted / solved all the challenges!\n\n"
        else:
            username = user.data.get("username")
            if username and username != "":
                ctf_menu_msg += f"Welcome {username}:\n\n"
            ctf_menu_msg += f"""🔥 Capture The Flag (CTF) Challenges\n\n"""

        score_type_msg = "final" if (
            all_challenges_completed or not challenges_to_attempt) else "current"
        ctf_menu_msg += MESSAGE_DIVIDER
        ctf_menu_msg += f"""Your {score_type_msg} score is: <u><b>{ctf_state["total_score"]} points</b></u>\n"""
        ctf_menu_msg += MESSAGE_DIVIDER + "\n\n"

        # ctf_menu_msg += "✅ - You have completed this challenge\n\n"
        # ctf_menu_msg += "❌ - You can no longer attempt this  challenge\n\n"
        # ctf_menu_msg += "<b>Challenge Types:</b>\n\n"
        # ctf_menu_msg += "⚠️ - Single-try challenge, you can only attempt once\n\n"
        # ctf_menu_msg += "⌛️ - Time based challenge, timer will begin upon first viewing of the challenge.\n\n"

        reply_markup = InlineKeyboardMarkup(keyboard)

        self.bot.edit_or_reply_message(
            update, context,
            ctf_menu_msg,
            reply_markup=reply_markup
        )

        return self.MENU

    def view_challenge(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        challenge_number = int(query.data.split('_')[-1])

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_CTF_VIEW_CHALLENGE_{challenge_number}",
                         f"User:{user.chatid} has viewed Challenge {challenge_number}")
        ctf_state = user.data.get("ctf_state")

        challenge = ctf_state["challenges"][challenge_number]

        if challenge["time_based"] and not challenge["time_based"]["start_time"]:
            delay_before_revealing = 5
            for i in range(delay_before_revealing):
                self.bot.edit_or_reply_message(
                    update, context,
                    "This is a ⌛️ time-based challenge! \nThe faster you solve it, the more points you will receive."
                    + "\n\nTimer will start as soon as challenge is revealed!\n\n"
                    + MESSAGE_DIVIDER +
                    f"Revealing challenge in: <b>{delay_before_revealing-i}</b>",
                )
                time.sleep(1)

            # Updating and saving players data
            challenge["time_based"].update(
                {"start_time": datetime.datetime.now()})
            user.save_user_to_file()

        self.display_challenge(update, context, challenge_number)

        return self.CHALLENGE_VIEW

    def reveal_hint(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer(do_nothing=True)

        query_info = query.data.split('_')[-1].split(':')
        hint_number, challenge_number = query_info
        challenge_number, hint_number = int(challenge_number), int(hint_number)

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_CTF_VIEW_HINT_{challenge_number}_{hint_number}",
                         f"User:{user.chatid} has revealed hint {hint_number} for Challenge {challenge_number}")
        ctf_state = user.data.get("ctf_state")

        # Updating and saving players data
        challenge = ctf_state["challenges"][challenge_number]
        hint = challenge["hints"][hint_number]

        hint.update({"used": True})
        challenge.update(
            {"total_hints_deduction": challenge["total_hints_deduction"] + hint["deduction"]})
        user.save_user_to_file()

        self.display_challenge(update, context, challenge_number)

        return self.CHALLENGE_VIEW

    def submit_choice_answer(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        query_info = query.data.split('_')[-1].split(':')
        choice_number, challenge_number = query_info
        challenge_number, choice_number = int(
            challenge_number), int(choice_number)

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_CTF_SUBMIT_{challenge_number}",
                         f"User:{user.chatid} is submitting choiced answer {choice_number} for Challenge {challenge_number}")
        ctf_state = user.data.get("ctf_state")

        challenge = ctf_state["challenges"][challenge_number]
        choice = challenge["multiple_choices"][choice_number]

        return self.check_answer(update, context, challenge_number, choice.lower())

    def submit_answer(self, update: Update, context: CallbackContext) -> USERSTATE:
        is_first_attempt = update.callback_query.message.text.find('❌') == -1

        query = update.callback_query
        query.answer(keep_message=is_first_attempt)

        challenge_number = int(query.data.split('_')[-1])

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_CTF_SUBMIT_{challenge_number}",
                         f"User:{user.chatid} is submitting answer for Challenge {challenge_number}")

        if is_first_attempt:
            if not self.bot.behavior_remove_inline_markup:
                query.message.edit_reply_markup()

            self.bot.edit_or_reply_message(
                update, context,
                text="Enter you answer:",
                reply_message=True
            )
        else:
            self.bot.edit_or_reply_message(
                update, context,
                text="Enter you answer:"
            )
        context.user_data.update(
            {"ctf_message_handler_debounce": challenge_number})
        return self.SUBMIT_CHALLENGE

    def handle_answer(self, update: Update, context: CallbackContext) -> USERSTATE:
        challenge_number = context.user_data.get(
            "ctf_message_handler_debounce")
        if challenge_number is not None and update.message is not None and update.message.text is not None:
            context.user_data.pop("ctf_message_handler_debounce")

            return self.check_answer(
                update, context,
                challenge_number,
                utils.format_input_str(update.message.text.lower(), True, "@_")
            )
        else:
            return self.SUBMIT_CHALLENGE

    def view_leaderboard(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        user.logger.info(f"USER_CTF_VIEW_LEADERBOARd",
                         f"User:{user.chatid} is viewing the leaderboard.")
        ctf_state = user.data.get("ctf_state")

        ctf_user_placing = False
        text_body = ""

        text_body += f"<b><u>LEADERBOARD (TOP {MAX_LEADERBOARD_VIEW})</u></b>\n\n"

        if len(self.leaderboard) > 0:
            updated_leaderboard = False

            for idx, placing_array in enumerate(self.leaderboard):
                total_score, top_users = placing_array

                text_body += (
                    "🥇" if idx == 0 else
                    "🥈" if idx == 1 else
                    "🥉" if idx == 2 else
                    f" {idx + 1}) "
                )

                placing_text = " "

                for top_user in top_users:
                    if top_user == user:
                        placing_text = "⭐️ <b>You</b>," + placing_text
                        ctf_user_placing = idx
                    else:
                        top_user_name = top_user.data.get("username")

                        # Leaderboard is stale due to admin modifying in-memory data
                        if top_user_name == '' and not updated_leaderboard:
                            updated_leaderboard = True
                            self.update_leaderboard()

                        placing_text += top_user_name
                        placing_text += ", "

                # Gets rid of the trailing ,\n
                if placing_text[-2] == ",":
                    placing_text = placing_text[:-2]

                text_body += placing_text
                text_body += f"  |  <u>{total_score} points</u>\n\n"

            if updated_leaderboard:
                text_body += "\n\n⚠️ OUTDATED. Re-open Leaderboard from Menu. ⚠️\n\n"
        else:
            text_body += "🦗 It appears no one has gotten any points yet...\n\n"

        text_body += "\n"

        text_body += MESSAGE_DIVIDER
        text_body += f"""Your current score is: <u><b>{ctf_state["total_score"]} points</b></u>\n"""
        if ctf_user_placing is not False:
            text_body += f"🏆 You placed #{ctf_user_placing + 1}\n"
        text_body += MESSAGE_DIVIDER

        self.bot.edit_or_reply_message(
            update, context,
            text=text_body,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("« Back to Menu", callback_data="ctf_return_to_menu")]])
        )
        return self.LEADERBOARD_VIEW
    # -

    def display_challenge(self, update: Update, context: CallbackContext, challenge_number: int) -> None:
        user: User = context.user_data.get("user")
        ctf_state = user.data.get("ctf_state")

        challenge = ctf_state["challenges"][challenge_number]
        is_challenge_completed = challenge["completed"]
        hints_exist = len(challenge["hints"]) > 0
        can_attempt = (challenge["one_try"] and challenge["attempts"] == 0) or (
            not challenge["one_try"])
        is_multiple_choices = challenge["multiple_choices"]

        keyboard = []
        text_body = f"<b>Challenge {challenge_number+1}</b>: "

        total_points_deduction = int(challenge["total_hints_deduction"])
        challenge_points = int(challenge["points"])
        number_of_attempts = int(challenge["attempts"]) + 1

        effective_score = challenge_points

        if is_multiple_choices:
            effective_score = effective_score / number_of_attempts
        effective_score = int(max(effective_score - total_points_deduction, 0))

        if not is_challenge_completed:
            text_body += f"<u>Up to {effective_score} points</u>\n\n"

            if challenge["time_based"]:
                pass
                # keyboard.append([InlineKeyboardButton("Refresh points", callback_data=f"ctf_refresh_challenge_{challenge_number}")])
            if can_attempt and not is_multiple_choices:
                keyboard.append([InlineKeyboardButton(
                    "Submit answer", callback_data=f"ctf_submit_answer_{challenge_number}")])
            # Creates the RevealHint and  SubmitFlag buttons if challenge is not completed

            if is_multiple_choices:
                idx = 0
                for t_idx, choice in enumerate(challenge["multiple_choices"]):
                    if idx % 2 == 0:
                        keyboard.append([])
                    idx += 1

                    keyboard[-1].append(
                        InlineKeyboardButton(
                            f"{choice}", callback_data=f"ctf_select_choice_{t_idx}:{challenge_number}")
                    )

            idx = 0
            for t_idx, hint in enumerate(challenge["hints"]):
                # Only create a button for RevealHint if the hint is not yet revealed
                if not hint["used"]:
                    if idx % 2 == 0:
                        keyboard.append([])
                    idx += 1

                    keyboard[-1].append(
                        InlineKeyboardButton(
                            f"""Hint {t_idx+1} (-{hint["deduction"]} points)""", callback_data=f"ctf_view_hint_{t_idx}:{challenge_number}")
                    )
        else:
            text_body += f"You earned <u>{effective_score} points</u>\n\n"
            # if is_multiple_choices and total_points_deduction > 0:
            #     text_body += f"(points / attempts) - hints = <u>{effective_score} points</u>\n\n"
            # elif total_points_deduction > 0:
            #     text_body += f"points - hints = <u>{effective_score} points</u>\n\n"
            # else:
            #     text_body += f"<u>{effective_score} points</u>\n\n"

        # Create the BackToMenu button
        keyboard.append([InlineKeyboardButton(
            "« Back", callback_data="ctf_return_to_menu")])

        # if challenge["time_based"]:
        #     max_time_seconds = int(challenge["time_based"]["limit"])
        #     max_hint_deductions = int(challenge["max_hints_deduction"])
        #     start_time : datetime = challenge["time_based"]["start_time"]
        #     end_time = challenge["time_based"]["end_time"] or datetime.datetime.now()

        #     diff = end_time - start_time
        #     seconds_taken = max(0, min(diff.total_seconds() , max_time_seconds)) # Clamp the value for time taken to max allocated time

        #     points_to_award = challenge_points - ((seconds_taken / max_time_seconds) * (challenge_points - max_hint_deductions))
        #     challenge_points = int(points_to_award)

        # challenge_points -= total_points_deduction
        # challenge_points = challenge_points if challenge_points >= 0 else 0
        # if challenge["time_based"] or hints_exist:
        #     text_body += f"(<b><u>{challenge_points}</u></b> is what you'll receive)\n\n"
        # else:
        #     text_body += "\n\n"

        text_body += challenge["description"]
        if challenge["additional_info"]:
            text_body += f"""\n\n<i>Note: {challenge["additional_info"]}</i>"""
        text_body += "\n\n\n"
        # Displays the URLs to the files needed for the challenge (if any, so if there's nothing this part is skipped)
        if hints_exist or len(challenge["files"]) > 0:
            if len(challenge["files"]) > 0:
                text_body += "<i>Download the files here:</i>\n"
                for file_link in challenge["files"]:
                    text_body += file_link + "\n"
                text_body += "\n\n"

            if hints_exist:
                if is_challenge_completed and challenge["total_hints_deduction"] > 0:
                    text_body += "Hints used:\n"
                for t_idx, hint in enumerate(challenge["hints"]):
                    is_hint_used = hint["used"]

                    # Displays the hints depending on whether they have been used else placeholder text is used
                    if not is_challenge_completed or is_hint_used:
                        text_body += MESSAGE_DIVIDER
                        text_body += f"Hint {t_idx+1}: "

                        text_body += f"""<b>{hint["text"]}</b>""" if is_hint_used else "Click button below to reveal."
                        if is_challenge_completed:
                            text_body += f"""\n(<u>-{hint["deduction"]} points</u>)"""
                        text_body += "\n"
                        text_body += MESSAGE_DIVIDER

        if is_challenge_completed:
            text_body += "\n✅ <b>YOU HAVE COMPLETED THIS CHALLENGE!</b> ✅"
        elif not can_attempt:
            text_body += "\n❌ <b>YOU CAN LONGER ATTEMPT THIS CHALLENGE!</b> ❌"
        elif challenge["one_try"]:
            text_body += "\n⚠️ <b>ONLY ONE ATTEMPT ALLOWED!</b> ⚠️"
        elif challenge["time_based"]:
            pass
            # text_body += "\n⌛️ <b>THIS IS A TIME BASED CHALLENGE!</b> ⌛️"

        self.bot.edit_or_reply_message(
            update, context,
            text=text_body,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    def check_answer(self, update: Update, context: CallbackContext, challenge_number: int, answer: str) -> USERSTATE:
        user: User = context.user_data.get("user")
        ctf_state = user.data.get("ctf_state")
        challenge = ctf_state["challenges"][challenge_number]

        answer_key = challenge["answer"].lower()
        challenge["attempts"] += 1

        if answer == answer_key:
            challenge["completed"] = True

            challenge_points = int(challenge["points"])

            if challenge["time_based"]:
                max_time_seconds = int(challenge["time_based"]["limit"])
                max_hint_deductions = int(challenge["max_hints_deduction"])

                start_time: datetime = challenge["time_based"]["start_time"]
                end_time = datetime.datetime.now()

                diff = end_time - start_time
                # Clamp the value for time taken to max allocated time
                seconds_taken = max(
                    0, min(diff.total_seconds(), max_time_seconds))

                points_to_award = challenge_points - \
                    ((seconds_taken / max_time_seconds) *
                     (challenge_points - max_hint_deductions))
                challenge_points = int(points_to_award)

                challenge["time_based"]["end_time"] = end_time
            elif challenge["multiple_choices"]:
                challenge_points = int(
                    challenge_points / challenge["attempts"])

            challenge_points -= int(challenge["total_hints_deduction"])
            challenge_points = challenge_points if challenge_points >= 0 else 0
            ctf_state["total_score"] += challenge_points
            ctf_state.update({"last_score_update": datetime.datetime.now()})

            user.save_user_to_file()
            self.update_leaderboard()

            user.logger.info(f"USER_CTF_CORRECT_ANSWER_{challenge_number}",
                             f"""User:{user.chatid} @{ctf_state["total_score"]}@ got the answer CORRECT for Challenge {challenge_number}""")

            text_body = f"✅  Congratulations on solving Challenge {challenge_number+1} 🎉🥳\n\n"
            text_body += f"Points earned: <b>{challenge_points}</b>\n"
            text_body += MESSAGE_DIVIDER
            text_body += f"""Your current score is: <u><b>{ctf_state["total_score"]} points</b></u>\n"""
            text_body += MESSAGE_DIVIDER + "\n"
            # text_body += "Press the button below to return to menu."

            self.bot.edit_or_reply_message(
                update, context,
                text=text_body,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("« Back to Menu", callback_data="ctf_return_to_menu")]])
            )
            return self.CHALLENGE_SUCCESS
        else:
            user.save_user_to_file()
            user.logger.info(f"USER_CTF_WRONG_ANSWER_{challenge_number}",
                             f"""User:{user.chatid} @{answer}@ got the answer WRONG for Challenge {challenge_number}""")

            text_body = f"""❌ Your answer: <u>{answer}</u> is <b>incorrect</b>.\n\n"""

            if answer_key.find("flag@") > -1 and (len(answer) < 5 or answer[:5].lower() != "flag@"):
                text_body += MESSAGE_DIVIDER
                text_body += "⚠️ Your answer was not of the right format.\n"
                text_body += "Answer format: <b><u>flag@XXXXXX</u></b>.\n"
                text_body += (MESSAGE_DIVIDER + "\n")

            # if not challenge["one_try"]:
            #     text_body += "Don't give up and keep trying! 💪\n\n"
            #     text_body += "Use the buttons below to retry or head back to the menu to attempt other challenges."
            # else:
            #     text_body += "Aww its okay! 💪\n\n"
            #     text_body += "Use the button below to head back to the menu and attempt other challenges."

            keyboard = []
            if not challenge["one_try"]:
                if challenge["multiple_choices"]:
                    keyboard.append([InlineKeyboardButton(
                        f"Retry challenge", callback_data=f"ctf_return_to_challenge_{challenge_number}")])
                else:
                    keyboard.append([InlineKeyboardButton(
                        f"Retry challenge", callback_data=f"ctf_submit_answer_{challenge_number}")])
            keyboard.append([InlineKeyboardButton(
                "« Back to Menu", callback_data="ctf_return_to_menu")])

            self.bot.edit_or_reply_message(
                update, context,
                text=text_body,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            return self.CHALLENGE_WRONG

    def update_leaderboard(self, top_placing: int = MAX_LEADERBOARD_VIEW) -> list:
        if self.leaderboard_active:
            dict_scoring_list = {}
            scoring_list = []

            for _, user in self.users_manager.users.items():
                ctf_state = user.data.get("ctf_state")
                user_total_score = str(ctf_state["total_score"])

                if int(user_total_score) > 0:
                    if user_total_score not in dict_scoring_list:
                        dict_scoring_list.update({user_total_score: []})

                    dict_scoring_list[user_total_score].append(user)

            for total_score, users in dict_scoring_list.items():
                scoring_list.append([int(total_score), users])

            total_scores_count = len(scoring_list)
            top_placing = total_scores_count if top_placing > total_scores_count else top_placing

            scoring_list.sort(reverse=True, key=lambda a: a[0])
            # Cull the scoring list according to the top X that we want
            scoring_list = scoring_list[:top_placing]

            self.leaderboard = scoring_list
            return scoring_list
        else:
            return []
