import os
import re
def print_keys(d, parent_key=''):
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                print(new_key)
                print_keys(v, new_key)
            else:
                print(f"{new_key} - {v}")
def sanitize_filename(name):
    """Sanitize the category name to create a valid filename."""
    return re.sub(r'[\/:*?"<>|]', '_', name).strip()
def create_dir_if_not_exist(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory '{directory}' created.")
    else:
        print(f"Directory '{directory}' already exists.")

def create_file_if_not_exist(filepath):
    # Create the directory if it doesn't exist
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory '{directory}' created.")

    # Create the file if it doesn't exist
    if not os.path.exists(filepath):
        with open(filepath, 'w') as file:
            pass  # Just open and close the file to create it
        print(f"File '{filepath}' created.")
    else:
        print(f"File '{filepath}' already exists.")

def read_file(filename, settings_dir):
    with open(os.path.join(settings_dir, filename), 'r') as file:
        return file.read().strip()

def load_run_links(runs_file_path):
    if not os.path.exists(runs_file_path):
        return []
    with open(runs_file_path, 'r') as file:
        return file.read().splitlines()

def save_run_links(runs_file_path, run_links):
    with open(runs_file_path, 'w') as file:
        file.write("\n".join(run_links))

gameID_to_channelID = {
    'xkdk4g1m': 984959264168747075, #Jak1
    'nd28x9qd': 984959264168747075, #Jak1 OG
    'ok6qlo1g': 984959264168747076, #Jak2
    'xldeq5d3': 984959264428810240, #JakX
}

def get_text_channel_from_gameID(gameID):
    channel_id = gameID_to_channelID.get(gameID)
    if channel_id:
        return channel_id
    else:
        return 984959264428810244

game_name_to_short = {
    'Jak and Daxter: The Precursor Legacy': 'Jak 1',
    'OpenGOAL: Jak 1' : 'Jak 1 OG',
    'Jak II': 'Jak 2',
    'Jak 3': 'Jak 3',
    'Jak X: Combat Racing': 'Jak X',
    'Daxter': 'Daxter'
}

def get_short_game_name(full_game_name):
    short_name = game_name_to_short.get(full_game_name)
    if short_name:
        return short_name
    else:
        return full_game_name  # Return full name if no mapping exists

def capitalize_user_names(user_names):
    # Split the names by ' & ' and capitalize each name's first letter
    capitalized_names = " & ".join(name.strip().title() for name in user_names.split(' & '))
    return capitalized_names




if __name__ == "__main__":
    import bot