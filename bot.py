import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import discord
from discord.ext import tasks, commands
from discord import Embed, Intents, app_commands
from run import Run
from tasks import post_new_runs
from utils import read_file, load_run_links, save_run_links
import requests


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

    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hi, {interaction.user.mention}', ephemeral=True)

    async def post_Run_Manually(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hi this is a placeholder command and not implemented yet., {interaction.user.mention}', ephemeral=True)

    @tasks.loop(seconds=30)
    async def timer_task(self):
        print("trying to get new runs")
        await post_new_runs(self)

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
            await self.tree.sync()
            self.synced = True

        print(f'Logged in as {self.user.name}')
        self.timer_task.start()
        self.discord_channel = self.get_channel(self.discord_channel_id)


intents = Intents.default()
intents.messages = True
bot = RunBot(command_prefix=commands.when_mentioned_or('$'), intents=intents)

#print("Starting bot with token:", bot.token)
print("Starting bot")
bot.run(bot.token)
