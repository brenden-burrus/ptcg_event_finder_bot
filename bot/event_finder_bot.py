import os

import discord
from dotenv import load_dotenv
from backend.get_events import getEvents, run

from discord.ext import commands

#Load Environment Variables
load_dotenv()
TOKEN = os.get_env('DISCORD_TOKEN')


#instantiate Bot
bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


bot.run(TOKEN)