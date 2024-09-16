# Main Script
from classes.event_finder_class import PokemonEventFinder



event_finder_url = "https://events.pokemon.com/en-us/events?sort=when&near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_challenge,league_cup&maxDistance=50"


if __name__ == "__main__":
    events = PokemonEventFinder(event_finder_url)
    
    events.getEvents()
    