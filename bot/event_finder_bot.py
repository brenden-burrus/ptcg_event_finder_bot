import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from operator import itemgetter

from get_events import getEvents
from bot_functions import format_message, get_months


#Load Environment Variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')



test_list = [{'when': 'October 05, 2024 6:00PM', 'name': 'Grapes Games League Challenge', 'reg': 'September 19, 2024 3:30PM - October 05, 2024 6:00PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/bddd35a1095a1fe211502068a3b50232', 'address': '16431 VILLAGE PLAZA VIEW DR, WILDWOOD, MO 63011, USA', 'locality': '', 'phone': '6363453024', 'email': 'Grapesgcc@gmail.com', 'store': 'Grapes Games', 'month': 'October'}, {'when': 'November 10, 2024 12:00PM', 'name': 'Yeti Gaming TCG November League Challenge', 'reg': 'November 10, 2024 11:00AM - November 10, 2024 12:00PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/04073b1c87889f1165976c76764be54e', 'address': '84 GRASSO PLAZA, AFFTON, MO 63123, USA', 'locality': '', 'phone': '3147971075', 'email': 'zack@yetigaming.com', 'store': 'Yeti Gaming', 'month': 'November'}, {'when': 'October 06, 2024 12:00PM', 'name': 'Yeti TCG Oct League Challenge', 'reg': 'October 06, 2024 11:00AM - October 06, 2024 12:00PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/04073b1c87889f1165976c76764be54e', 'address': '84 GRASSO PLAZA, AFFTON, MO 63123, USA', 'locality': '', 'phone': '(314) 797-1075', 'email': 'zack@yetigaming.com', 'store': 'Yeti Gaming', 'month': 'October'}, {'when': 'September 28, 2024 10:00AM', 'name': 'Collector Store League Cup', 'reg': 'September 28, 2024 9:00AM - September 28, 2024 10:00AM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/6e5715e01099de44d96929023bd7b45a', 'address': '1106 JUNGS STATION RD', 'locality': 'ST PETERS, MO, US', 'phone': '6364777800', 'email': 'kmccarthy@collectorstore.com', 'store': 'Collector Store', 'month': 'September'}, {'when': 'September 27, 2024 6:15PM', 'name': 'Collector Store League Challenge', 'reg': 'September 27, 2024 5:30PM - September 27, 2024 6:10PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/6e5715e01099de44d96929023bd7b45a', 'address': '1106 JUNGS STATION RD', 'locality': 'ST PETERS, MO, US', 'phone': '6364777800', 'email': 'kmccarthy@collectorstore.com', 'store': 'Collector Store', 'month': 'September'}, {'when': 'September 28, 2024 2:00PM', 'name': 'SVLeagueChallenge', 'reg': 'September 28, 2024 1:00PM - September 28, 2024 2:00PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/46d210053344676c3d935baa240d3836', 'address': '258 FORT ZUMWALT SQUARE', 'locality': "O'FALLON, MO, US", 'phone': '636-294-7529', 'email': 'manticoregameshop@gmail.com', 'store': 'Manticore Game Shop', 'month': 'September'}, {'when': 'September 28, 2024 2:00PM', 'name': 'Washington Pokémon League Cup', 'reg': 'July 12, 2024 12:00PM - September 28, 2024 2:00PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/cc35c474b832458a329bea71f9dde420', 'address': '316 JEFFERSON ST', 'locality': 'WASHINGTON, MO, US', 'phone': '6364328081', 'email': 'marc.lampe012@gmail.com', 'store': 'Game Euphoria', 'month': 'September'}, {'when': 'September 22, 2024 2:00PM', 'name': 'Washington Pokémon League Challenge', 'reg': 'September 01, 2024 12:00AM - September 22, 2024 2:00PM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/cc35c474b832458a329bea71f9dde420', 'address': '316 JEFFERSON ST', 'locality': 'WASHINGTON, MO, US', 'phone': '6364328081', 'email': 'marc.lampe012@gmail.com', 'store': 'Game Euphoria', 'month': 'September'}, {'when': 'November 17, 2024 11:15AM', 'name': 'Oct - Dec League Cup 2024', 'reg': 'November 17, 2024 10:00AM - November 17, 2024 11:00AM', 'league_details': 'https://www.pokemon.com/us/pokemon-trainer-club/play-pokemon-leagues/1f993f57e8a2dd17ac91dbb872fa2dd9', 'address': '1005 CENTURY DR', 'locality': 'EDWARDSVILLE, IL, US', 'phone': '(618) 659-0099', 'email': 'cadenbug01@gmail.com', 'store': 'Heroic Adventures', 'month': 'November'}]
test_list = sorted(test_list, key = itemgetter('when'), reverse=True)

#instantiate Bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(name='events')
async def help_text(ctx):
    messageText = ""
    relevant_months = get_months(test_list)
    for month in relevant_months:
        messageText = messageText + f"# {month} League Cups and Challenges\n\n"
        for event in test_list:
            if event['month'] == month:
                messageText = messageText + format_message(event)

        await ctx.send(messageText)
        messageText = ""



bot.run(TOKEN)