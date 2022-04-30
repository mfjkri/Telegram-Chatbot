from calendar import c
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
        

EXPORTS_DIRECTORY = get_dir_or_create("exports")
LOGS_PATTERNS = {
    "date" : r"\b[0-9]+-[0-9]+-[0-9]+",
    "time" : r"\b[0-9]+:[0-9]+:[0-9]+",
    "date_time" : r"\b[0-9]+-[0-9]+-[0-9]+ +[0-9]+:[0-9]+:[0-9]+", 
    "action_code" : r"(?<=\$CODE::)[A-Z0-9_]+",
    "chatid" : r"(?<=User:)[0-9]+",
    "score" : r"(?<=@)[0-9]+(?=@)",
}


def extract_data_type_from_line(data_type : str, log_line : str) -> Union[str, None]:
    # 2022-04-28 14:22:46,376 [INFO] $CODE::USER_CTF_CORRECT_ANSWER_1 || User:1026217187 @40@ ____
    
    assert data_type in LOGS_PATTERNS, f"UNKNOWN OR MALFORMED DATA_TYPE LOOKUP: {data_type}"
    pattern = LOGS_PATTERNS[data_type]
        
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
                
                if user_data:
                    name, group = user_data.get("name"),user_data.get("group")
                    
                    with open(user_log_file, 'r') as stream:
                        user_logs = list((line.rstrip() for  line in stream.readlines()))
                        
                    users.update({
                        chatid : {
                            "name" : name,
                            "group" : group,
                            
                            "logs" : user_logs,
                            "data" : user_data,
                            
                            "log_file" : user_log_file,
                            "data_yaml_file" : user_data_yaml,
                        }
                    })        
    
    return users


def export_log_files(export_file_name : str) -> None:
    users = get_users()
    
    cached_scores = {} # A useful mapping dictionary to cache new score for next iterations
    
    #logs_by_time : A dictionary with key:time, value: array of logs
    #scores_by_time: A dictionary with key:time, value: dictionary with (key: chatid, value: score)
        # Used to keep track of changes in score and update cached_scores later when filling in gaps in logs (second iteration)
    #chatids_by_time: A dictionary with key:time, value: array of chatids
        # Used to keep track of which users have logs for which time and used to fill in logs for others who don't have for that time.
    logs_by_time, scores_by_time, chatids_by_time = {}, {}, {}
    compiled_logs = []
    
    for chatid, user in users.items():
        name, group = user["name"], user["group"]
        cached_scores.update({chatid : 0})
        
        for line in user["logs"]:
            log_time = extract_data_type_from_line("time", line)
                
            challenge_number = None
            score = 0
            action_keyword = extract_data_type_from_line("action_code", line)
            
            if action_keyword:
                action_keys = action_keyword.split("_")
                
                if "WRONG_ANSWER" in action_keyword or "CORRECT_ANSWER" in action_keyword:
                    challenge_number = int(action_keys[4]) + 1
                    if "CORRECT" in action_keyword:
                        score = int(extract_data_type_from_line("score", line))
                        cached_scores[chatid] = score
                        action_keyword = "CORRECT_ANSWER"
                    else:
                        action_keyword = "WRONG_ANSWER"
                elif "VIEW_HINT" in action_keyword:
                    challenge_number = int(action_keys[4]) + 1
                    action_keyword = f"VIEW_HINT_{int(action_keys[-1]) + 1}"
                elif "CREATING_NEW_USER" in action_keyword:
                    action_keyword = "INIT_USER"
                    challenge_number = 0
                    
                if challenge_number:
                    if not log_time in logs_by_time:
                        chatids_by_time.update({log_time : []})
                        logs_by_time.update({log_time : []})
                        scores_by_time.update({log_time : {}})
                    
                    logs_by_time[log_time].append(
                        f"{name},{group},{action_keyword},{challenge_number},{max(score, cached_scores[chatid])}"
                    )
                    
                    chatids_by_time[log_time].append(chatid)
                    if score != 0 or challenge_number == "INIT":
                        scores_by_time[log_time].update({chatid : score})
                    
    cached_scores = {}
    for time in sorted(chatids_by_time):
        chatids = chatids_by_time[time]
        for chatid, user in users.items():
            if chatid not in chatids:
                cached_scores[chatid] = cached_scores[chatid] if chatid in cached_scores else 0
                logs_by_time[time].append(
                    f"""{user["name"]},{user["group"]},FILL_DATA,,{cached_scores[chatid]}"""
                )
            elif chatid in scores_by_time[time] and scores_by_time[time][chatid] > 0:
                cached_scores[chatid] = scores_by_time[time][chatid]
    
    for time, logs in logs_by_time.items():
        [compiled_logs.append(f"{time},{log}\n") for log in logs]
    
    compiled_logs.sort(key=lambda x : x.split(',')[0])
    
    with open(os.path.join(EXPORTS_DIRECTORY, f"{export_file_name}.csv"), "w") as export_file:
        compiled_logs.insert(0, "TIME,NAME,GROUP,ACTION,CHALLENGE NUMBER, SCORE\n")
        export_file.writelines(compiled_logs)

    
if __name__ == "__main__":
    
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--export", type=str, help="Exports the log file for visualization.", default="", required=False)
    ARGS = PARSER.parse_args()
    
    export_log_files(ARGS.export or "exported_logs")