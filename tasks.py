from discord import Embed
from run import Run
from utils import print_keys, save_run_links
from datetime import timedelta
import config
import json
import os
from utils import *
import requests


async def post_new_runs(bot):
    print("in post_new_runs")
    runs = []
    for game_id in bot.game_ids:
        runs.extend(get_runs(bot, game_id))

    new_runs = get_new_runs(runs, bot.run_links)
    print("out of new_runs")
    for new_run in new_runs:
        embed = Embed(
            title=f"{new_run.user_names} has finished a run of {new_run.game_name or 'Unknown Game'}: {new_run.category_name} with a PB of {new_run.time}.",

            color=0x3498db
        )
        embed.set_footer(text=bot.bot_name)
        embed.set_thumbnail(url=bot.image_link)
        embed.set_thumbnail(url="https://www.speedrun.com/static/game/" + new_run.game_id + "/cover.png?v=c8fb842")
        embed.add_field(name="Players:", value=new_run.user_names)
        embed.add_field(name="Time:", value=str(new_run.time))
        embed.description = f"[Link]({new_run.link})"
        if config.Post_to_discord:
            print(f"gameID: {new_run.game_id}, channel_id: {get_text_channel_from_gameID(new_run.game_id)} url {new_run.link}")
            await bot.get_channel(get_text_channel_from_gameID(new_run.game_id)).send(embed=embed)
        #get_text_channel_from_gameID
    bot.run_links = [run.link for run in runs]
    save_run_links(bot.runs_file_path, bot.run_links)

#    async def post_Run_Manually(self, interaction: discord.Interaction, runid: str, forcepost: bool, skipdiscord: bool):
async def post_new_runs_manual(bot, runid, forcepost, skipdiscord):
    print("in post_new_runs_manual")
    runs = []
    runs.extend(get_runs(bot, get_game_id_from_runID(bot, runid)))

    new_runs = get_run_with_id(runs, bot.run_links, runid)
    #new_runs = get_all_runs_by_id(runs)
    print("out of single_runs")
    for new_run in new_runs:
        embed = Embed(
            title=f"{new_run.user_names} has finished a run of {new_run.game_name}: {new_run.category_name} with a PB of {str(new_run.time)}",
            color=0x3498db
        )
        embed.set_footer(text=bot.bot_name)
        embed.set_thumbnail(url=bot.image_link)
        embed.set_thumbnail(url="https://www.speedrun.com/static/game/" + new_run.game_id + "/cover.png?v=c8fb842")
        embed.add_field(name="Time Save From Previous Run: ", value=new_run.user_names)
        embed.add_field(name="Players:", value=new_run.user_names)
        embed.add_field(name="Time:", value=str(new_run.time))
        embed.description = f"[Link]({new_run.link})"
        if not skipdiscord:
            await bot.discord_channel.send(embed=embed)

    bot.run_links = [run.link for run in runs]
    save_run_links(bot.runs_file_path, bot.run_links)

def get_game_id_from_runID(bot, runid):
    response = bot.http_client.get(f'https://www.speedrun.com/api/v1/runs/{runid}')
    data = response.json()
    # Extract the game ID from the response
    game_id = data['data']['game']
    return game_id

def get_game_name(bot, game_id):
    url = f"https://www.speedrun.com/api/v1/games/{game_id}"
    response = bot.http_client.get(url)

    if response.status_code == 200:
        game_data = response.json()
        game_name = game_data['data']['names']['international']
        return game_name
    else:
        print(f"Failed to retrieve game name for game ID {game_id}. Status code: {response.status_code}")
        return None

def get_runs(bot, game_id):
    #response = bot.http_client.get(f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=new&embed=category,players')
    runs = []
    max_results = 200
    offset = 0

    while True:
        response = bot.http_client.get(f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=verified&embed=category,players&max={max_results}&offset={offset}')
        data = response.json()

        runs.extend(data['data'])

        if len(data['data']) < max_results:
            break  # No more runs to fetch

        offset += max_results
    return parse_runs(bot, response.json())

def get_new_runs(runs, existing_run_links):
    new_runs = []
    for run in runs:
        if run.link not in existing_run_links or not config.skip_known_runs:
            new_runs.append(run)
        else:
            0
            #print(f"Skipping run: {run.link} (already in existing run links)")
    return new_runs

def get_run_with_id(runs, existing_run_links, runId):
    new_runs = []
    matched = False
    unmatched_links = []

    for i, run in enumerate(runs):
        if run.run_id == runId:
            new_runs.append(run)
            print(f"Found matching run: {run.link} {run.run_id}")
            matched = True
        else:
            unmatched_links.append(f"#{i + 1} {run.link} {run.run_id}")

    if not matched:
        print(f"ERROR: Did not find match for runID {runId}. Run links were:")
        for link in unmatched_links:
            print(link)

    return new_runs

def get_all_runs_by_id(runs):
    new_runs = []
    for i, run in enumerate(runs):
        new_runs.append(run)
    return new_runs


def parse_runs(bot, json_data):
    runs = []
    for run in json_data['data']:
        link = run['weblink']
        user_names = capitalize_user_names(" & ".join(player['names']['international'] for player in run['players']['data']))
        #user_names = "Xyphles"
        time = timedelta(seconds=run['times']['primary_t'])
        game_id = run['game']
        game_name = get_short_game_name(get_game_name(bot, game_id))
        run_id = run['id']
        #print_keys(run)
        category_name = run['category']['data']['name']
        category_id = run['category']['data']['id']

        # host = f"https://www.speedrun.com/api/v1/leaderboards/{game_id}/category/{category_id}?embed=game,players,category.variables,level.variables"
        # print(f"\nFetching leaderboard for category: {category_name} ({category_id})")
        # print(host)

        # try:
        #     response = requests.get(host)
        #     response.raise_for_status()
        # except requests.exceptions.RequestException as e:
        #     print(f"HTTP error occurred: {e}")
        #     continue

        # try:
        #     json_data = response.json()["data"]
        # except (json.JSONDecodeError, KeyError) as e:
        #     print(f"Failed to parse JSON or find 'data' key: {e}")
        #     continue


        # runs = json_data.get("runs", [])
        # print(f"Number of runs in category '{category_name}':", len(runs))

        # map_of_runs = {}

        # for i, run_data in enumerate(runs):
        #     run_obj = run_data["run"]
        #     players_data = json_data["players"]["data"][i]

        #     ghost_src_account = "names" not in players_data.keys()

        #     current_run_id = run_obj["id"]
        #     current_game_id = run_obj["game"]
        #     current_category_id = json_data["category"]["data"]["id"]
        #     current_category_name = category_name
        #     current_game_name = json_data["game"]["data"]["names"]["international"]
        #     current_game_prefix = json_data["game"]["data"]["abbreviation"]
        #     current_game_image_url = json_data["game"]["data"]["assets"]["cover-large"]["uri"]
        #     current_place = run_data["place"]
        #     last_place = len(runs)
        #     current_placement_string = f"{current_place}/{last_place}"

        #     if not ghost_src_account:
        #         # Safely access 'names' and provide a default if not found
        #         names = players_data.get("names", {})
        #         current_player_name = names.get("international", "Unknown").capitalize()
        #         current_runner_src_profile_pic = players_data.get("assets", {}).get("image", {}).get("uri", "NONE")
        #     else:
        #         current_player_name = "ghostSRCaccount"
        #         current_runner_src_profile_pic = "NoSrcAccount"

        #     # Formatting the time
        #     primary_time = run_obj["times"]["primary_t"]
        #     time_delta = timedelta(seconds=primary_time)
        #     current_formatted_time_string = str(time_delta)

        #     # Check if there's a video link
        #     video_url = None
        #     if "videos" in run_obj and run_obj["videos"] and "links" in run_obj["videos"]:
        #         video_url = run_obj["videos"]["links"][0]["uri"]

        #     run = {
        #         "runID": current_run_id,
        #         "categoryName": current_category_name,
        #         "gameName": current_game_name,
        #         "runnerSrcProfilePic": current_runner_src_profile_pic,
        #         "gameID": current_game_id,
        #         "categoryID": current_category_id,
        #         "gameImageURL": current_game_image_url,
        #         "videolink": video_url,
        #         "place": current_placement_string,
        #         "purePlace": current_place,
        #         "time": current_formatted_time_string,
        #         "playerName": current_player_name,
        #         "prefix": current_game_prefix
        #     }

        #     map_of_runs[current_run_id] = run
        # game_dir = sanitize_filename(game_name)
        # # Save the category data to a JSON file in the directory
        # category_filename = os.path.join(game_dir, f"{sanitize_filename(category_name)}.json")
        # with open(category_filename, 'w') as json_file:
        #     json.dump(map_of_runs, json_file, indent=4)
        # print(f"Data for category '{category_name}' saved to {category_filename}")

    print("Data saved into separate JSON files.")

    runs.append(Run(link, user_names, time, category_name, game_id, run_id, game_name))
    return runs

def create_category_json(bot, game_id):
    url = f"https://www.speedrun.com/api/v1/games/{game_id}/categories"
    response = bot.http_client.get(url)
    categories_data = response.json()['data']

    categories_info = {}
    for category in categories_data:
        category_id = category['id']
        category_name = category['name']

        subcategories_url = f"https://www.speedrun.com/api/v1/categories/{category_id}/variables"
        sub_response = bot.http_client.get(subcategories_url)
        subcategories_data = sub_response.json()['data']

        subcategories = {}
        for subcategory in subcategories_data:
            if subcategory['is-subcategory']:
                # Check structure and log potential issues
                print(f"Subcategory raw data: {subcategory}")

                # Correcting to use 'values' instead of 'choices'
                if 'values' in subcategory and 'values' in subcategory['values']:
                    subcategories[subcategory['name']] = [
                        value['label'] for value in subcategory['values']['values'].values()
                    ]
                else:
                    print(f"Unexpected subcategory structure: {subcategory}")


        categories_info[category_name] = {
            "id": category_id,
            "subcategories": subcategories
        }

    game_info = {
        "selected_game_id": game_id,
        "categories": categories_info
    }

    file_path = os.path.join(bot.settings, "configs", game_id, f"categories.json")
    create_file_if_not_exist(file_path)
    file_path = os.path.join(bot.settings, "configs", game_id, f"_{get_game_name(bot, game_id)}.txt")
    create_file_if_not_exist(file_path)
    with open(file_path, "w") as f:
        json.dump(game_info, f, indent=4)


if __name__ == "__main__":
    import bot