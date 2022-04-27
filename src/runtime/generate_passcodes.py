import os, random, string

from datetime import datetime

stages_folder = os.path.join("src", "stages")

def strip_string_constructors(s : str) -> str:
    return ''.join([char for char in s if char not in '",'])

def generate_passcodes(new_users : list) -> None:
    authenticate_py_file = os.path.join(stages_folder, "authenticate.py")
    
    assert os.path.isfile(authenticate_py_file), "authenticate.py not found"
    
    raw_data = {}
    with open(authenticate_py_file, 'r') as stream:
        raw_data = stream.readlines()
        
    start_marker_idx, end_marker_idx = False, False
    for idx, line in enumerate(raw_data):
        if "# START_OF_PASSCODES_MARKER" in line:
            start_marker_idx = idx
        elif "# END_OF_PASSCODES_MARKER" in line:
            end_marker_idx = idx
            break
    
    current_passcodes = {}
    new_passcodes = {}
    
    assert start_marker_idx is not False, "START marker missing from Authenticate.PASSCODES"
    assert end_marker_idx is not False, "END marker missing from Authenticate.PASSCODES"
    
    for idx in range(start_marker_idx + 1, end_marker_idx - 1):
        line = raw_data[idx]
        line = ''.join(char for char in line if (char != '#' and char != ' ' and char != '\n'))
        marker = line.find(':')
        
        if marker > 0:
            passcode = strip_string_constructors(line[:marker])
            registered_user = strip_string_constructors(line[marker+1:])
            current_passcodes.update({passcode : registered_user})
    
    
    for user in new_users:
        random_passcode = ""
        
        while random_passcode == "" or random_passcode in current_passcodes:
            possible_letters = "ABCDEFGHJKMNPQRSTWXYZ" #string.ascii_uppercase - (I, L, O, U, V)
            letter = random.choices(possible_letters, k=1)
            numbers = random.choices(string.digits, k=4)
            numbers[:] = [str(x) for x in numbers]
            
            random_passcode = ''.join(letter) + ''.join(numbers)
        
        current_passcodes.update({user : random_passcode})
        new_passcodes.update({user : random_passcode})
    
    raw_data.insert(end_marker_idx, "\t#------\n")            
    for user, new_passcode in new_passcodes.items():
        raw_data.insert(end_marker_idx, f"""\t"{new_passcode}" : "{user}",\n""")
    raw_data.insert(end_marker_idx, "\t# Refer to src.runtime.generate_passcodes for more details.\n\n")            
    raw_data.insert(end_marker_idx, f"""\t# Generated at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n""")            
    raw_data.insert(end_marker_idx, "\n\t#------\n")            
    
    with open(authenticate_py_file, 'w') as active_ctf_file:
        active_ctf_file.writelines(raw_data)
            
        
if __name__ == "__main__":
    generate_passcodes(
        [
            "Johnny Smith",
            "Muhammad Fikri"
        ]
    )