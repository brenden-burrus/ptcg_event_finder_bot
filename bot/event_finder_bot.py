import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from operator import itemgetter
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

from get_events import getCupsChallenges
import bot_functions as F

CUP_LIST = []
CHALLENGE_LIST = []


#Load Environment Variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')


#instantiate Bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


def get_events():
    try:
        global CUP_LIST
        global CHALLENGE_LIST
        CUP_LIST, CHALLENGE_LIST = getCupsChallenges()
        
        CUP_LIST = sorted(CUP_LIST, key=itemgetter('when'), reverse=True)
        CHALLENGE_LIST = sorted(CHALLENGE_LIST, key=itemgetter('when'), reverse=True)
    except:
        print(f"Error occured while getting events {datetime.datetime.now()}")
    return


scheduler = BackgroundScheduler()
scheduler.add_job(get_events, "cron", day_of_week="0-6", hour=1)
# scheduler.add_job(send_events, "cron", day_of_week="0,2", hour=12)
scheduler.start()


#initial_run
get_events()


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='events')
async def send_events(ctx):
    messageText = ""
    if "cup" in ctx.channel.name:
        relevant_months = F.get_months(CUP_LIST)
        await F.delete_old_messages(ctx, bot.user.id, F.get_months(CUP_LIST))
        for month in relevant_months:
            messageText = messageText + f"# __{month} League Cups__\n\n"
            for event in CUP_LIST:
                if event['month'] == month:
                    messageText = messageText + F.format_message(event)
            await ctx.send(messageText)
            messageText = ""
    elif "challenge" in ctx.channel.name:
        relevant_months = F.get_months(CHALLENGE_LIST)
        await F.delete_old_messages(ctx, bot.user.id, F.get_months(CHALLENGE_LIST))
        for month in relevant_months:
            messageText = messageText + f"# __{month} League Challenges__\n\n"
            for event in CHALLENGE_LIST:
                if event['month'] == month:
                    messageText = messageText + F.format_message(event)
            await ctx.send(messageText)
            messageText = ""
    else:
        relevant_months = F.get_months(CHALLENGE_LIST + CUP_LIST)
        await F.delete_old_messages(ctx, bot.user.id, F.get_months(CHALLENGE_LIST + CUP_LIST))
        for month in relevant_months:
            messageText = messageText + f"# *{month} League Cups and Challenges*\n\n"
            for event in CHALLENGE_LIST + CUP_LIST:
                if event['month'] == month:
                    messageText = messageText + F.format_message(event)
            await ctx.send(messageText)
            messageText = ""


bot.run(TOKEN)