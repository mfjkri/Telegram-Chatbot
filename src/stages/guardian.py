import time

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (CallbackQueryHandler, CallbackContext)

from user import UserManager, User
from bot import (Bot, USERSTATE, MESSAGE_DIVIDER)

QUESTIONS = {
    "blue": [
        "Triage and Investigate of cyber incidents",
        "Use threat intelligence to improve security posture",
        "Stop zero-day exploits and cyber crimes",
        "Contain and remediate incidents"
    ],
    "red": [
        "Exploit web applications to find flaws and weaknesses",
        "Analyze web traffic to discover security issues",
        "Developing scripts to bypass system controls",
        "Analyse and research into malware and social engineering"
    ],
    "yellow": [
        "Design layered defenses around business and risk requirements",
        "Implement technologies for prevention and response",
        "Analyze security architecture for deficiencies",
        "Roll out appropriate network and server security solutions"
    ]
}
TEAMS_DESC = {
    "red": {
        "icon": "⚔️",
        "title": "Attack Team",
        "desc": "You assume the role of a hacker in identifying an attack path that breaches the organization's security defense.",
    },
    "blue": {
        "icon": "🛡",
        "title": "Defend Team",
        "desc": "You are responsible for defending the organization use of information systems by maintaining its security posture against attackers.",
    },
    "yellow": {
        "icon": "🔎",
        "title": "Consultancy / Project Management Team",
        "desc": "You work to plan activities that are designed to reduce risk of exploitation by hackers and help the organization thrive.",
    }
}
DEFAULT_TEAM = "red"
TOTAL_QUESTIONS = len(QUESTIONS[DEFAULT_TEAM])
NUMER_OF_OPTIONS_PER_QUESTION = len(QUESTIONS.keys())

# --------------------------------- FEATURES --------------------------------- #
# - A range of questions and options to find users aptitude in cybersecurity
# - Dynamically created based on QUESTIONS, TEAMS_DSEC
# - Displays results at the end of questionaire
# - Handles ties in aptitude

# ----------------------------------- USAGE ---------------------------------- #
# Requirements:
# -

# Example of usage:
# --
# in ../${rootDir}/main.py:

# from bot import Bot
# from stages.guardian import Guardian

# def main():
#   ...
#
#   bot = Bot()
#   bot.init(BOT_TOKEN, logger)
#
#   STAGE_GUARDIAN = "guardian"
#
#   guardian: Guardian = Guardian(bot)
#   guardian.setup(
#       stage_id=STAGE_GUARDIAN,
#       next_stage_id=NEXT_STAGE
#   )
#
#   ...
#
# --

# ---------------------------------------------------------------------------- #


class Guardian(object):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.user_manager: UserManager = UserManager()

        self.stage = None
        self.states = []
        self.stage_id = None
        self.next_stage_id = None

        bot.add_custom_stage_handler(self)
        self.init_users_data()

    def init_users_data(self) -> None:
        guardian_state = {
            "teams": [],
            "teams.history": [],
            "options_picked": []
        }

        self.user_manager.add_data_field("guardian_state", guardian_state)

    def entry_guardian(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        return self.intro_view(update, context)

    def exit_guardian(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id=self.next_stage_id,
            update=update, context=context
        )

    def setup(self, stage_id: str, next_stage_id: str = "end") -> None:
        self.stage_id = stage_id
        self.next_stage_id = next_stage_id

        questions_text = [
            "Which of the following appeals to you the most?",
            "I am most interested in ________?",
            "Which would you like to do the most?",
            "Which of the following interest you the most?",
        ]
        options_text = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

        for i in range(0, TOTAL_QUESTIONS):
            current_question_id = f"guardian:qn:{i}"

            choices = []
            question_text = f"<b>Q{i + 1}) {questions_text[i%4]}</b>\n"
            question_text += MESSAGE_DIVIDER + "\n"

            option_idx = 0
            for team, options in QUESTIONS.items():
                option_text = options_text[option_idx]

                question_text += f"({option_text}) {options[i]}\n\n"
                choices.append({
                    "text": option_text,
                    "callback": lambda update, context, i=i, team=team: self.option_selected(update, context, i, team)
                })
                option_idx += 1

            self.bot.let_user_choose(
                choice_label=current_question_id,
                choice_text=question_text,
                choices=choices,
                choices_per_row=3
            )

        self.stage = self.bot.add_stage(
            stage_id=stage_id,
            entry=self.entry_guardian,
            exit=self.exit_guardian,
            states={
                "INTRO_VIEW": [
                    CallbackQueryHandler(
                        self.load_guardian, pattern="^guardian_begin$", run_async=True),
                    CallbackQueryHandler(
                        self.skip_guardian, pattern="^guardian_skip$", run_async=True)
                ],
                "RESULTS_VIEW": [
                    CallbackQueryHandler(
                        self.exit_guardian, pattern="^guardian_finished$", run_async=True)
                ]
            }
        )
        self.states = self.stage["states"]
        self.INTRO_VIEW, self.RESULTS_VIEW = self.bot.unpack_states(
            self.states)

    def option_selected(self,
                        update: Update, context: CallbackContext,
                        question_number: int, option_selected: str) -> USERSTATE:
        user: User = context.user_data.get("user")
        guardian_state = user.data.get("guardian_state")

        guardian_state["options_picked"].append(option_selected)
        user.save_user_to_file()

        if question_number < TOTAL_QUESTIONS - 1:
            if not self.bot.behavior_remove_inline_markup:
                self.bot.edit_or_reply_message(
                    update, context,
                    "💭 Loading next question..."
                )
                time.sleep(0.25)
            return self.bot.proceed_next_stage(
                current_stage_id=f"choose:guardian:qn:{question_number}",
                next_stage_id=f"choose:guardian:qn:{question_number + 1}",
                update=update, context=context
            )
        else:
            self.calculate_results(update, context)
            return self.display_results(update, context)

    def skip_guardian(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        return self.exit_guardian(update, context)

    def intro_view(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        guardian_state = user.data.get("guardian_state")

        text_body = f"""Welcome {user.data.get("username")}.\n\n"""
        text_body += "Let's answer a few questions and discover what kind of Cyber Guardian you are!"

        keyboard = [InlineKeyboardButton(
            "Begin", callback_data="guardian_begin")]

        if len(guardian_state.get("teams", [])) > 0 or len(guardian_state.get("teams.history", [])) > 0:
            if len(guardian_state.get("teams", [])) == 0:
                guardian_state.update(
                    {"teams": list(guardian_state.get("teams.history"))})
                user.save_user_to_file()

            keyboard.append(InlineKeyboardButton(
                "Skip", callback_data="guardian_skip"))

        self.bot.edit_or_reply_message(
            update, context,
            text=text_body,
            reply_markup=InlineKeyboardMarkup([keyboard]),
        )

        return self.INTRO_VIEW

    def load_guardian(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        query.answer()

        user: User = context.user_data.get("user")
        guardian_state = user.data.get("guardian_state")

        guardian_state["options_picked"] = []
        guardian_state["teams"] = []
        user.save_user_to_file()

        return self.bot.proceed_next_stage(
            current_stage_id=self.stage_id,
            next_stage_id="choose:guardian:qn:0",
            update=update, context=context
        )

    def calculate_results(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        guardian_state = user.data.get("guardian_state")
        teams_picked = []

        teams_dict, teams_list = {}, []

        for team_selected in guardian_state["options_picked"]:
            teams_dict.update(
                {team_selected: teams_dict.get(team_selected, 0) + 1})

        for team, repetition in teams_dict.items():
            teams_list.append([repetition, team])
        teams_list.sort(key=lambda a: a[0], reverse=True)

        teams_picked.append(teams_list[0][1])
        if len(teams_list) > 1 and teams_list[0][0] == teams_list[1][0]:
            teams_picked.append(teams_list[1][1])

        user.logger.info(
            "USER_IS_TEAM", f"User:{user.chatid} has gotten the results of {teams_picked}")

        guardian_state.update({"teams": list(teams_picked)})
        guardian_state.update({"teams.history": list(teams_picked)})
        user.save_user_to_file()

    def display_results(self, update: Update, context: CallbackContext) -> USERSTATE:
        query = update.callback_query
        if query:
            query.answer()

        user: User = context.user_data.get("user")
        guardian_state = user.data.get("guardian_state")
        teams_picked = guardian_state.get("teams")

        text_body = "You are most interested in:\n\n"

        for team_name in teams_picked:
            team = TEAMS_DESC[team_name]
            text_body += f"""<b><u>{team["title"]}</u> {team["icon"]}</b>\n{team["desc"]}\n\n\n"""

        self.bot.edit_or_reply_message(
            update, context,
            text="💭 Displaying your results..."
        )
        time.sleep(0.25)

        self.bot.edit_or_reply_message(
            update, context,
            text=text_body,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Next", callback_data="guardian_finished"),
                ]
            ])
        )
        return self.RESULTS_VIEW
