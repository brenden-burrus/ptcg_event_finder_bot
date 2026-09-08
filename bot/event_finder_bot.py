import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from operator import itemgetter
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

from get_events import getLocalEvents
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
        CUP_LIST, CHALLENGE_LIST = getLocalEvents()
        
        CUP_LIST = sorted(CUP_LIST, key=itemgetter('date'), reverse=False)
        CHALLENGE_LIST = sorted(CHALLENGE_LIST, key=itemgetter('date'), reverse=False)
    except:
        print(f"Error occured while getting events {datetime.datetime.now()}")

    print(CUP_LIST)
    print("--------------------------------")
    print(CHALLENGE_LIST)
    
    return
    


scheduler = BackgroundScheduler()
scheduler.add_job(get_events, "cron", day_of_week="0-6", hour=1)
scheduler.start()


#initial_run
get_events()


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


def events_for_channel(channel_name):
    """Which tournaments a channel asks for, and what to call them."""
    if "cup" in channel_name:
        return CUP_LIST, "League Cups"
    if "challenge" in channel_name:
        return CHALLENGE_LIST, "League Challenges"
    return CHALLENGE_LIST + CUP_LIST, "League Cups and Challenges"


@bot.command(name='events')
async def send_events(ctx):
    events, tier = events_for_channel(ctx.channel.name)
    relevant_months = F.get_months(events)
    print(relevant_months)
    await F.delete_old_messages(ctx, bot.user.id, relevant_months)

    for month in reversed(relevant_months):
        this_month = [event for event in events
                      if event['date'].split(' ')[1] == month]
        # A month with more tournaments than one Discord message can hold comes
        # back as several messages. Every one of them carries the month in its
        # header, which is what lets the next Refresh find them all -- ADR-0001.
        posts = F.build_month_posts(
            f"{month} {tier}", [F.format_message(event) for event in this_month]
        )
        print(f"Total message length for {month} {tier}: "
              f"{sum(len(post) for post in posts)} across {len(posts)} message(s)")
        for post in posts:
            await ctx.send(post)


bot.run(TOKEN)