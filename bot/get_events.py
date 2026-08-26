from event_finder_class import PokemonEventFinder
import datetime


def getLocalEvents():
    current_time = datetime.datetime.now()
    search_date = str(current_time.strftime('%Y-%m-%d'))
    search_location = "St. Louis, MO, USA"
    event_finder_url = f"https://events.pokemon.com/EventLocator/Home?iskm=false&range=50&SortDistance=true&locale=en-US&startdate={search_date}&filters=league_cup,league_challenge,tcg"
    events_class = PokemonEventFinder(event_finder_url, search_location)
    
    events_class.getEvents()

    return events_class.cup_dicts, events_class.challenge_dicts


if __name__ == "__main__":
    getLocalEvents()
