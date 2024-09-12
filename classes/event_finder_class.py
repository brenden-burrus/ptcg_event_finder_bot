# Contains the class that handles getting scrapted data from the Pokemon Event Finder

import time
import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class PokemonEventFinder:
    def __init__(self, url) -> None:
        self.url = url
        self.events = []
        self.soup = ''

    
    def getEvents(self):
        driver = webdriver.Chrome()
        driver.get(self.url)
        time.sleep(3)
        page = driver.page_source
        driver.quit()
        self.soup = bs4.BeautifulSoup(page, 'lxml')
