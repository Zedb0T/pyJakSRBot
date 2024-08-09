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