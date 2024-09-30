from event_finder_class_2 import PokemonEventFinder
import datetime
from dateutil.relativedelta import relativedelta


def initializeEventFinderClass(url):
    return PokemonEventFinder(url)


def getCups():
    current_time = datetime.datetime.now()
    current_time += relativedelta(months=+3)
    search_date = str(current_time.strftime('%m/%d/%Y'))
    event_finder_url = f"https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_cup&maxDistance=50&maxDate={search_date}"
    events_class = initializeEventFinderClass(event_finder_url)
    
    events_class.getEvents("cup")

    return events_class.league_table_dicts


def getChallenges():
    current_time = datetime.datetime.now()
    current_time += relativedelta(months=+3)
    search_date = current_time.strftime('%m/%d/%Y')
    event_finder_url = f"https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_challenge&maxDistance=50&maxDate={search_date}"
    events_class = initializeEventFinderClass(event_finder_url)
    
    events_class.getEvents("challenge")

    return events_class.league_table_dicts


def getCupsChallenges():
    current_time = datetime.datetime.now()
    current_time += relativedelta(months=+3)
    search_date = current_time.strftime('%m/%d/%Y')
    cups_url = f"https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_cup&maxDistance=50&maxDate={search_date}"
    challenges_url = f"https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_challenge&maxDistance=50&maxDate={search_date}"

    cup_event_class = initializeEventFinderClass(cups_url)
    challenge_event_class = initializeEventFinderClass(challenges_url)

    cup_event_class.getEvents("cup")
    challenge_event_class.getEvents("challenge")

    return cup_event_class.league_table_dicts, challenge_event_class.league_table_dicts


if __name__ == "__main__":
    cups = getCups()
    print(cups)