import os
import argparse
import logging
import subprocess
import sys


def get_dir_or_create(dir_str: str, to_log: bool = False) -> str:
    dir_path = os.path.join(dir_str)
    if not os.path.isdir(dir_path):
        if to_log:
            log.info(f"Directory: {dir_str} not found. Creating one...")
        os.mkdir(dir_path)
    return dir_path


if __name__ == "__main__":

    is_windows, is_linux = "win32" in sys.platform, "linux" in sys.platform

    log = logging.getLogger("CSA_Telegram_Bot setup")
    log.setLevel(10)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    terminal_output = logging.StreamHandler(sys.stdout)
    terminal_output.setFormatter(formatter)
    log.addHandler(terminal_output)

    log_file = logging.FileHandler(f"project_setup.log")
    log_file.setFormatter(formatter)
    log.addHandler(log_file)

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "--setup", type=str, help="Sets up project. Creates venv and install require modules.", default="", required=False)
    ARGS = PARSER.parse_args()

    if ARGS.setup != "":

        prjDir = os.getcwd()
        log.info(f"Changing working directory to: {prjDir}")
        os.chdir(prjDir)

        # -------------------- Creating directories -------------------- #
        log.info("Creating exports and logs directories...")
        get_dir_or_create("exports", True)
        get_dir_or_create("logs", True)

        log.info("Creating users directory...")
        users_directory = get_dir_or_create("users", True)

        log.info("Creating ctf/challenges directories...")
        ctf_directory = get_dir_or_create("ctf", True)
        get_dir_or_create(os.path.join(ctf_directory, "challenges"), True)

        banned_users_yaml_file = os.path.join(
            users_directory, "banned_users.yaml")
        with open(banned_users_yaml_file, "w") as file:
            file.writelines([""])
        # ------------------------------------- - ------------------------------------ #

        python_ver_keyword = ARGS.setup
        python_version = subprocess.check_output(
            [python_ver_keyword, "--version"], shell=is_windows)
        log.info(f"PYTHON VERSION BEING USED IS: {python_version}")

        # ---------------------------- Creating python env --------------------------- #
        log.info(f"Creating python venv (if already exists, nothing happens)...")
        subprocess.run([python_ver_keyword, "-m", "venv", "venv"])
        # ------------------------------------- - ------------------------------------ #

        # ------------------------- Creating config.yaml file ------------------------ #
        try:
            with open("config.yaml") as config_file:
                log.info("config.yaml file already exits. Skipping this part...")
        except IOError:
            log.info(
                f"No config.yaml file found! Creating one with default template...")
            with open("config.yaml", "w") as config_file:
                config_file.writelines(
                    [
                        "# ---------------------------------- RUNTIME --------------------------------- #\n"
                        "RUNTIME:\n"
                        "  LIVE_MODE: false\n",
                        "  FRESH_START: false\n\n",

                        "# -------------------------------- BOT CONFIG -------------------------------- #\n",
                        "BOT_TOKENS:\n",
                        "  LIVE: TOKEN_HERE\n",
                        "  TEST: TOKEN_HERE\n\n",

                        "BOT:\n",
                        "  REMOVE_INLINE_KEYBOARD_MARKUP: False\n\n",

                        "# ------------------------------ USER PASSCODES ------------------------------ #\n"
                        "MAKE_ANONYMOUS: false\n\n",

                        "USER_PASSCODES:\n",
                        "  # START_OF_PASSCODES_MARKER\n\n"

                        "  A1234: John Smith\n\n"

                        "  # END_OF_PASSCODES_MARKER\n\n"

                        "# ------------------------------ ADMIN CHATIDS ------------------------------ #\n"
                        "ADMIN_CHATIDS: []\n\n",

                        "# -------------------------------- LOG CONFIG -------------------------------- #\n",
                        "LOG_USER_TO_APP_LOGS: false\n",
                    ]
                )
        # ------------------------------------- - ------------------------------------ #

        # ----------------- Modify shebang in main.py to relativepath ---------------- #
        log.info(f"Setting shebang of main.py to venv intepreter...")
        data = None
        main_py_file = os.path.join("main.py")
        with open(main_py_file, 'r', encoding="utf-8") as main_py:
            data = main_py.readlines()

        if is_linux:
            data[0] = f"#!{os.path.join(prjDir, 'venv', 'bin', python_ver_keyword)}\n"
        elif is_windows:
            data[0] = f"#!{os.path.join(prjDir, 'venv', 'Scripts', f'{python_ver_keyword}.exe')}\n"
        else:
            data[0] = f"#SETUP_ERROR: Operating system shebang format unknown."
        with open(main_py_file, 'w', encoding="utf-8") as main_py:
            main_py.writelines(data)
        # ------------------------------------- - ------------------------------------ #

        if is_linux:

            # ---------------------- Giving program executable perm ---------------------- #
            log.info(f"Setting main.py to be an executable...")
            subprocess.run(["sudo", "chmod", "u+x", "main.py"])
            # ------------------------------------- - ------------------------------------ #

            # -------------------------- Installing dependencies ------------------------- #
            log.info(
                f"Installing dependencies from requirements.txt into venv now...")
            subprocess.run([os.path.join("venv", "bin", python_ver_keyword),
                           "-m", "pip", "install", "-r", "requirements.txt"])
            #subprocess.run([f"venv/bin/{python_ver_keyword}", "-m", "pip", "install", "-r", "requirements.txt"])
            # ------------------------------------- - ------------------------------------ #

        elif is_windows:

            # -------------------------- Installing dependencies ------------------------- #
            log.info(
                f"Installing dependencies from requirements.txt into venv now...")
            subprocess.run([os.path.join(
                "venv", "Scripts", f"{python_ver_keyword}.exe"), "-m", "pip", "install", "-r", r".\requirements.txt"], shell=True)
            # ------------------------------------- - ------------------------------------ #

        elif "darwin" in sys.sys.platform:
            log.error(
                "setup.py currently does not support installing of dependencies. Please do this manually.")
