import os

def print_keys(d, parent_key=''):
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                print(new_key)
                print_keys(v, new_key)
            else:
                print(f"{new_key} - {v}")

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

if __name__ == "__main__":
# Import the bot.py script
    import bot