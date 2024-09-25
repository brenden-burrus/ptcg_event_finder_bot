from event_finder_class import PokemonEventFinder


def initializeEventFinderClass(url):
    return PokemonEventFinder(url)


def getCups():
    event_finder_url = "https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_cup&maxDistance=50"
    events_class = initializeEventFinderClass(event_finder_url)
    
    events_class.getEvents()

    return events_class.event_dicts


def getChallenges():
    event_finder_url = "https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_challenge&maxDistance=50"
    events_class = initializeEventFinderClass(event_finder_url)
    
    events_class.getEvents()

    return events_class.event_dicts


def getCupsChallenges():
    cups_url = "https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_cup&maxDistance=50"
    challenges_url = "https://events.pokemon.com/en-us/events?near=Manchester,%20MO,%20USA&filters=tcg,tournament,league_challenge&maxDistance=50"

    cup_event_class = initializeEventFinderClass(cups_url)
    challenge_event_class = initializeEventFinderClass(challenges_url)

    cup_event_class.getEvents()
    challenge_event_class.getEvents()

    return cup_event_class.event_dicts, challenge_event_class.event_dicts


if __name__ == "__main__":
    cups = getCups()
    challenges = getChallenges()
