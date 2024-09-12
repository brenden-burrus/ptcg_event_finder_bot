# Contains the class that handles getting scrapted data from the Pokemon Event Finder

import requests
import bs4

class PokemonEventFinder:
    def __init__(self, url) -> None:
        self.url = url
        self.events = []
        self.request = ''
        self.soup = ''

    
    def getEvents(self):
        self.request = requests.get(self.url)
        self.soup = bs4.BeautifulSoup(self.request.text, 'lxml')
