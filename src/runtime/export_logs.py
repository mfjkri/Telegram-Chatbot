import os, argparse, re
from typing import Union

import yaml

#TODO:
# Allow export of logs -> data for BOTH archived_ctfs and active_ctf
# Just store all the usernames at runtime instead of per user and caching the result
# Add ability of export logs -> question data instead of user-centric
    # So something like  { challenge_number | action_keywords | attempts | solved | hint_1| hint_2 }"

def get_dir_or_create(dir_path : str) -> str:
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    return os.path.join(dir_path)


def load_yaml_file(file_path : str) -> Union[bool, dict]:
    with open(file_path, 'r') as stream:
        config = {}
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError:
            config = False
        return config
        

patterns = {
    "date" : r"\b[0-9]+-[0-9]+-[0-9]+",
    "time" : r"\b[0-9]+:[0-9]+:[0-9]+",
    "date_time" : r"\b[0-9]+-[0-9]+-[0-9]+ +[0-9]+:[0-9]+:[0-9]+", 
    "action_code" : r"(?<=\$CODE::)[A-Z0-9_]+",
    "chatid" : r"(?<=User:)[0-9]+",
    "total_score" : r"(?<=@)[0-9]+(?=@)",
}
def extract_data_type_from_line(data_type : str, log_line : str) -> Union[str, None]:
    # 2022-04-28 14:22:46,376 [INFO] $CODE::USER_CTF_CORRECT_ANSWER_1 || User:1026217187 @40@ ____
    
    assert data_type in patterns, "UNKNOWN OR MALFORMED DATA_TYPE LOOKUP"
    pattern = patterns[data_type]
        
    matches = re.search(pattern, log_line)
    return matches.group(0) if matches else None
        

def get_users() -> dict:
    users = {}
    
    users_directory = os.path.join(os.getcwd(), "users")
    for chatid in os.listdir(users_directory):
        user_directory = os.path.join(users_directory, chatid)
        if os.path.isdir(user_directory): 
            user_data_yaml = os.path.join(user_directory, f"{chatid}.yaml")
            user_log_file = os.path.join(user_directory, f"{chatid}.log")
            
            if os.path.isfile(user_data_yaml) and os.path.isfile(user_log_file):
                user_logs = None
                user_data = load_yaml_file(user_data_yaml)
                
                with open(user_log_file, 'r') as stream:
                    user_logs = list((line.rstrip() for  line in stream.readlines()))
                    
                users.update({
                    chatid : {
                        "logs" : user_logs,
                        "data" : user_data,
                        
                        "log_file" : user_log_file,
                        "data_yaml_file" : user_data_yaml,
                    }
                })        
    
    return users


def export_log_files(export_file_name : str) -> None:
    users = get_users()
    
    compiled_logs_by_time = {}
    
    for chatid, user in users.items():
        for line in user["logs"]:
            log_time = extract_data_type_from_line("time", line)
            
            if not log_time in compiled_logs_by_time:
                compiled_logs_by_time.update({log_time : []})
                
            challenge_number = None
            action_keyword = extract_data_type_from_line("action_code", line)
            action_keys = action_keyword.split("_")
            
            if "WRONG_ANSWER" in action_keyword or "CORRECT_ANSWER" in action_keyword:
                challenge_number = action_keys[2]
            elif "VIEW_HINT" in action_keyword:
                challenge_number = action_keys[-3]
            elif "CREATING_NEW_USER" in action_keyword:
                challenge_number = "INIT"
                
            if challenge_number:
                print(line)
    
    
if __name__ == "__main__":
    
    exports_directory = get_dir_or_create("exports")
    logs_directory = "logs"
    if not os.path.isdir(logs_directory):
        raise "Logs directory not found."    
    
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--export", type=str, help="Exports the log file for visualization.", default="", required=False)
    ARGS = PARSER.parse_args()
    
    export_log_files(ARGS.export or "exported_logs")