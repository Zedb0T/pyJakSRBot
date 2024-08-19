import os
import discord
from discord.ext import commands, tasks
from discord import Intents, app_commands
import requests
import asyncio
import json
from tasks import *
from utils import read_file, load_run_links, save_run_links, create_dir_if_not_exist, create_file_if_not_exist

class RunBot(commands.Bot):
    def __init__(self, command_prefix, intents, **options):
        super().__init__(command_prefix, intents=intents, **options)
        self.synced = False
        self.settings_dir = os.path.join(os.getcwd(), "settings")
        self.token = read_file("discord.token", self.settings_dir)
        self.runs_file_path = os.path.join(self.settings_dir, "runs.link")
        self.run_links = load_run_links(self.runs_file_path)
        self.game_ids = read_file("game.ids", self.settings_dir).splitlines()
        self.bot_name = read_file("bot.name", self.settings_dir)
        self.image_link = read_file("image.link", self.settings_dir)
        self.discord_channel_id = int(read_file("discord.channel", self.settings_dir))
        self.timer_interval = int(read_file("timer.interval", self.settings_dir)) * 1000
        self.http_client = requests.Session()
        self.http_client.headers.update({'Cache-Control': 'no-cache'})
        self.command_queue = asyncio.Queue()

    async def command_processor(self):
        while True:
            command = await self.command_queue.get()
            try:
                await command()
            except Exception as e:
                print(f"Error processing command: {e}")
            finally:
                self.command_queue.task_done()

    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hi, {interaction.user.mention}', ephemeral=True)

    async def post_Run_Manually(self, interaction: discord.Interaction, runid: str, forcepost: bool, skipdiscord: bool):
        role_name = "Coder"
        has_role = any(role.name == role_name for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("You do not have the required role to use this command.", ephemeral=True)
            return
        await interaction.response.send_message("Processing your request, please wait...", ephemeral=True)
        await self.command_queue.put(lambda: post_new_runs_manual(self, runid, forcepost, skipdiscord))

    @tasks.loop(seconds=30)
    async def timer_task(self):
        countdown_seconds = 30
        while countdown_seconds > 0:
            print(f"Next check in {countdown_seconds} seconds...", end='\r')
            await asyncio.sleep(1)
            countdown_seconds -= 1

        print("\nTrying to get new runs...")
        # await post_new_runs(self)

    async def on_ready(self):
        if not self.synced:
            self.tree.add_command(
                app_commands.Command(
                    name="manual_post_run",
                    description="Manually take in a SRC url and post the embed",
                    callback=self.post_Run_Manually,
                )
            )
            self.tree.add_command(
                app_commands.Command(
                    name="heloo",
                    description="Bot just say hi :)",
                    callback=self.hello,
                )
            )
            self.tree.add_command(
                app_commands.Command(
                    name="select_game",
                    description="Search for a game on Speedrun.com and select it",
                    callback=self.select_game,
                )
            )
            await self.tree.sync()
            self.synced = True

        print(f'Logged in as {self.user.name}')

    async def select_game(self, interaction: discord.Interaction, game_name: str):
        url = f"https://www.speedrun.com/api/v1/games?name={game_name}&max=5"
        response = self.http_client.get(url)
        data = response.json()

        if not data['data']:
            await interaction.response.send_message(f"No games found for '{game_name}'", ephemeral=True)
            return

        choices = [
            app_commands.Choice(name=game['names']['international'], value=game['id'])
            for game in data['data']
        ]
        await interaction.response.send_message(
            content="Please select a game:",
            view=GameSelectionView(choices, interaction, self),
            ephemeral=True
        )

        self.loop.create_task(self.command_processor())
        for guild in bot.guilds:
            create_dir_if_not_exist("settings/" + str(guild.id))
            create_file_if_not_exist("settings/" + str(guild.id) + "/__" + guild.name + ".txt")
        self.timer_task.start()
        self.discord_channel = self.get_channel(self.discord_channel_id)

    async def on_message(self, message):
        if message.author == self.user:
            return

        print(f'New message from {message.author}: {message.content}')
        if message.content == "!bot poop":
            await message.channel.send("POOOOP")
        await self.process_commands(message)


class GameSelectionView(discord.ui.View):
    def __init__(self, choices, interaction, bot):
        super().__init__()
        self.interaction = interaction
        self.bot = bot
        self.add_item(GameSelectionDropdown(choices, interaction, bot))

class GameSelectionDropdown(discord.ui.Select):
    def __init__(self, choices, interaction, bot):
        options = [discord.SelectOption(label=choice.name, value=choice.value) for choice in choices]
        super().__init__(placeholder="Choose a game...", options=options)
        self.interaction = interaction
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        selected_game_id = self.values[0]
        guild_id = interaction.guild.id
        self.bot.settings_dir = os.path.join(self.bot.settings_dir, str(guild_id))
        url = f"https://www.speedrun.com/api/v1/games/{selected_game_id}/categories"
        response = self.bot.http_client.get(url)
        data = response.json()

        categories = [
            {"id": cat['id'], "name": cat['name']}
            for cat in data['data']
        ]

        await interaction.response.send_message(
            content="Please select categories:",
            view=CategorySelectionView(categories, interaction, self.bot, selected_game_id),
             ephemeral=True
        )


class CategorySelectionView(discord.ui.View):
    def __init__(self, categories, interaction, bot, game_id):
        options = [discord.SelectOption(label="All Categories", value="all")] + [discord.SelectOption(label=cat['name'], value=cat['id']) for cat in categories]
        super().__init__()
        self.add_item(CategorySelectionDropdown(options, interaction, bot, game_id))

class CategorySelectionDropdown(discord.ui.Select):
    def __init__(self, choices, interaction, bot, game_id):
        super().__init__(placeholder="Choose categories...", options=choices, max_values=len(choices))
        self.interaction = interaction
        self.bot = bot
        self.game_id = game_id

    async def callback(self, interaction: discord.Interaction):
        selected_values = self.values
        categories = {}
        if "all" in selected_values:
            url = f"https://www.speedrun.com/api/v1/games/{self.game_id}/categories"
            response = await self.bot.loop.run_in_executor(None, self.bot.http_client.get, url)
            data = response.json()

            for category in data['data']:
                categories[category['id']] = {
                    "name": category['name'],
                    "subcategories": await self.get_subcategories(category['id'])
                }
        else:
            for category_id in selected_values:
                url = f"https://www.speedrun.com/api/v1/categories/{category_id}"
                response = await self.bot.loop.run_in_executor(None, self.bot.http_client.get, url)
                category = response.json()
                categories[category_id] = {
                    "name": category['data']['name'],
                    "subcategories": await self.get_subcategories(category_id)
                }

        settings_dir = bot.settings_dir
        file_path = os.path.join(settings_dir, "configs", f"{self.game_id}.json")
        create_dir_if_not_exist(settings_dir)
        create_file_if_not_exist(file_path)
        # Convert sets to lists for JSON serialization
        def convert_to_serializable(data):
            if isinstance(data, set):
                return list(data)
            elif isinstance(data, dict):
                return {k: convert_to_serializable(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [convert_to_serializable(i) for i in data]
            else:
                return data

        serializable_data = {
            "selected_game_id": self.game_id,
            "categories": convert_to_serializable(categories)
        }

        with open(file_path, "w") as f:
            json.dump(serializable_data, f, indent=4)

        await interaction.response.send_message(f"Selected categories saved to {file_path}", ephemeral=True)

    async def get_subcategories(self, category_id):
        url = f"https://www.speedrun.com/api/v1/categories/{category_id}/variables"
        response = await self.bot.loop.run_in_executor(None, self.bot.http_client.get, url)
        data = response.json()

        subcategories = {}
        for subcategory in data['data']:
            subcategories[subcategory['id']] = {
                "name": subcategory['name'],
                "values": list(subcategory['values']['values'].values())  # Convert set to list
            }

        return subcategories

intents = Intents.default()
intents.messages = True
intents.message_content = True
bot = RunBot(command_prefix=commands.when_mentioned_or('$'), intents=intents)

print("Starting bot")
bot.run(bot.token)