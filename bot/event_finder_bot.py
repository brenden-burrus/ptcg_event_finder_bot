import os
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv
from operator import itemgetter
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

from event_finder_class import cleanup_past_events
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


def keep_previous_events(reason):
    """Hold on to the tournaments already stored, and say why.

    A failed scrape used to leave the bot with nothing to post until the next
    night. Yesterday's tournaments are better than none, but only after the
    ones that have since happened are dropped: retained data ages, and
    advertising a tournament that already took place is worse than saying
    nothing. The reason goes to the terminal alone -- a user in the channel
    sees an ordinary, slightly stale schedule, which is nothing they could act
    on anyway.
    """
    global CUP_LIST
    global CHALLENGE_LIST
    print(f"{reason} {datetime.datetime.now()}: "
          f"keeping the tournaments from the last good scrape")
    CUP_LIST = cleanup_past_events(CUP_LIST)
    CHALLENGE_LIST = cleanup_past_events(CHALLENGE_LIST)


def get_events():
    global CUP_LIST
    global CHALLENGE_LIST
    try:
        cup_list, challenge_list = getLocalEvents()
    # Exception rather than a bare except: the process runs for months, and
    # swallowing KeyboardInterrupt and SystemExit here traps whoever is trying
    # to stop it mid-scrape.
    except Exception:
        # The two failures are named apart because they need different fixes:
        # this one means the scraper is broken.
        keep_previous_events("Error occured while getting events")
        traceback.print_exc()
    else:
        if not cup_list and not challenge_list:
            # ...and this one is most likely a genuinely quiet week -- #8: a
            # scrape finding nothing is a legitimate outcome, not an error.
            keep_previous_events("No tournaments found")
        else:
            CUP_LIST = sorted(cup_list, key=itemgetter('date'), reverse=False)
            CHALLENGE_LIST = sorted(challenge_list, key=itemgetter('date'), reverse=False)

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
    events, label = events_for_channel(ctx.channel.name)
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
            f"{month} {label}", [F.format_message(event) for event in this_month]
        )
        print(f"Total message length for {month} {label}: "
              f"{sum(len(post) for post in posts)} across {len(posts)} message(s)")
        for post in posts:
            await ctx.send(post)


bot.run(TOKEN)