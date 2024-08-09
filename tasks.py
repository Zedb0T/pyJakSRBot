from discord import Embed
from run import Run
from utils import print_keys, save_run_links
from datetime import timedelta
import config

async def post_new_runs(bot):
    print("in post_new_runs")
    runs = []
    for game_id in bot.game_ids:
        runs.extend(get_runs(bot, game_id))

    new_runs = get_new_runs(runs, bot.run_links)
    print("out of new_runs")
    for new_run in new_runs:
        embed = Embed(
            title=f"A new '{new_run.category_name}' run is awaiting verification",
            color=0x3498db
        )
        embed.set_footer(text=bot.bot_name)
        embed.set_thumbnail(url=bot.image_link)
        embed.set_thumbnail(url="https://www.speedrun.com/static/game/" + new_run.game_id + "/cover.png?v=c8fb842")
        embed.add_field(name="Players:", value=new_run.user_names)
        embed.add_field(name="Time:", value=str(new_run.time))
        embed.description = f"[Link]({new_run.link})"
        if config.Post_to_discord:
            await bot.discord_channel.send(embed=embed)

    bot.run_links = [run.link for run in runs]
    save_run_links(bot.runs_file_path, bot.run_links)

def get_runs(bot, game_id):
    response = bot.http_client.get(f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=new&embed=category,players')
    #response = bot.http_client.get(f'https://www.speedrun.com/api/v1/runs?game={game_id}&status=verified&embed=category,players')
    return parse_runs(response.json())

def get_new_runs(runs, existing_run_links):
    new_runs = []
    for run in runs:
        if run.link not in existing_run_links or not config.skip_known_runs:
            new_runs.append(run)
        else:
            print(f"Skipping run: {run.link} (already in existing run links)")
    return new_runs



def parse_runs(json_data):
    runs = []
    for run in json_data['data']:
        link = run['weblink']
        user_names = " & ".join(player['names']['international'] for player in run['players']['data'])
        #user_names = "Xyphles"
        time = timedelta(seconds=run['times']['primary_t'])
        category_name = run['category']['data']['name']
        game_id = run['game']
        print_keys(run)
        runs.append(Run(link, user_names, time, category_name, game_id))
    return runs

if __name__ == "__main__":
# Import the bot.py script
    import bot