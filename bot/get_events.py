from event_finder_class import PokemonEventFinder
import datetime


def initializeEventFinderClass(url):
    return PokemonEventFinder(url)


def getLocalEvents():
    current_time = datetime.datetime.now()
    search_date = str(current_time.strftime('%Y-%m-%d'))
    event_finder_url = f"https://events.pokemon.com/EventLocator/Home?latitude=38.62742799999999&longitude=-90.1982439&iskm=false&range=50&SortDistance=true&locale=en-US&startdate={search_date}&filters=league_cup,league_challenge,tcg"
    events_class = initializeEventFinderClass(event_finder_url)
    
    events_class.getEvents()

    return events_class.cup_dicts, events_class.challenge_dicts


if __name__ == "__main__":
    getLocalEvents()
