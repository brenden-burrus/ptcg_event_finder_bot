import os
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

from event_finder_class import tournament_date, upcoming_tournaments
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


def keep_previous_tournaments(reason):
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
    CUP_LIST = upcoming_tournaments(CUP_LIST)
    CHALLENGE_LIST = upcoming_tournaments(CHALLENGE_LIST)


def get_events():
    global CUP_LIST
    global CHALLENGE_LIST
    try:
        cup_list, challenge_list = getLocalEvents()
        # Ordering by the day a tournament happens, not by the rendered date
        # string, which sorts by weekday name -- #19. A date the parser cannot
        # read raises somewhere in here (the scrape's own past-tournament
        # filter reads them first), which is why the sort belongs inside the
        # try: unusable dates are a failed scrape, handled like any other.
        cup_list = sorted(cup_list, key=tournament_date)
        challenge_list = sorted(challenge_list, key=tournament_date)
    # Exception rather than a bare except: the process runs for months, and
    # swallowing KeyboardInterrupt and SystemExit here traps whoever is trying
    # to stop it mid-scrape.
    except Exception:
        # A scrape that raises means the scraper is broken, so the traceback is
        # the useful part. The two failures are worded apart on the terminal
        # because they call for different responses from the owner.
        keep_previous_tournaments("Error occurred while getting events")
        traceback.print_exc()
    else:
        if not cup_list and not challenge_list:
            # A scrape that runs and finds nothing is most likely a quiet week,
            # not a fault -- #8: finding no tournaments is a legitimate outcome.
            keep_previous_tournaments("No tournaments found")
        else:
            CUP_LIST = cup_list
            CHALLENGE_LIST = challenge_list

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
    # Each list is in date order, but running one after the other is not: that
    # put every League Challenge before every League Cup whatever the dates
    # were -- #19. Merging them needs the sort again.
    return sorted(CHALLENGE_LIST + CUP_LIST, key=tournament_date), \
        "League Cups and Challenges"


@bot.command(name='events')
async def send_events(ctx):
    events, label = events_for_channel(ctx.channel.name)
    relevant_months = F.get_months(events)
    print(relevant_months)
    await F.delete_old_messages(ctx, bot.user.id, relevant_months)

    # The months now arrive in date order, so posting them in reverse leaves
    # the nearest month as the last message in the channel -- the one a reader
    # sees without scrolling. Before #19 this order was whatever the scrape
    # happened to produce; it is a choice now, so changing it is one too.
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