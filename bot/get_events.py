# Main Script
from classes.event_finder_class import PokemonEventFinder


def initializeEventFinderClass(url):
    return PokemonEventFinder(url)


def getEvents(events_class: object):
    event_finder_url = "https://events.pokemon.com/en-us/events?sort=when&near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_challenge,league_cup&maxDistance=50"
    events_class = initializeEventFinderClass(event_finder_url)
    
    events_class.getEvents()

    return events_class.event_dicts()