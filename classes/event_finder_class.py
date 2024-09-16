# Contains the class that handles getting scrapted data from the Pokemon Event Finder

import time
import bs4
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert

class PokemonEventFinder:
    def __init__(self, url) -> None:
        self.url = url
        self.events = []
        self.soup = ''
        self.debug_text = ''

    
    def getHTML(self):
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        event_urls = []
        driver.get(self.url)
        time.sleep(3)
        button_list = driver.find_elements(By.CLASS_NAME, "event-card")
        for i in range(len(button_list)):
            buttons = driver.find_elements(By.CLASS_NAME, "event-card")
            buttons[i].click()
            time.sleep(5)
            self.getEventInfo(driver.page_source)
            driver.back()
            time.sleep(5)

        driver.quit()
        print(event_urls)
        self.getEventInfo(event_urls)

    def getEventInfo(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        league = soup.find(id='league-detail-view')
        print(league.find(class_='event-header'))




    def getEvents(self):
        self.getHTML()
        # self.debug_text = self.soup.find_all(class_="event-card tournament tagged-event tagged-event-card")
        # for item in self.debug_text:
        #     address = item.find(class_="address")
        #     print(address)
        #     location = item.find(class_="location")
        #     print(location)
        #     date = item.find(class_='when')
        #     print(date)
        #     event_name = item.find(class_='event-header')
        #     print(event_name)