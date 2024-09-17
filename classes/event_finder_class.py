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
        self.events_html = []
        self.event_dicts = []

    
    def websiteNav(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        driver.get(self.url)
        time.sleep(5)
        button_list = driver.find_elements(By.CLASS_NAME, "event-card")
        for i in range(len(button_list)):
            buttons = driver.find_elements(By.CLASS_NAME, "event-card")
            buttons[i].click()
            time.sleep(10)
            self.getEventHTML(driver.page_source)
            driver.back()
            time.sleep(10)

        driver.quit()


    def getEventHTML(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        league = soup.find(id='league-detail-view')
        self.events_html.append(league)


    def extractEventInfo(self, event_soup):
        temp_dict = {}
        # print(event_soup.find(class_='event-header').get_text())
        temp_dict['when'] = event_soup.find(class_='when').get_text()
        temp_dict['name'] = event_soup.find(class_='event-header').get_text()
        temp_dict['reg'] = event_soup.find(class_='registration-time').get_text().replace('All Divisions', '')
        temp_dict['league_details'] = event_soup.find(class_='event_playtimes').find('a', href=True)['href']
        temp_dict['address'] = event_soup.find(class_='address').get_text()
        if event_soup.find(class_='locality') != None:
            temp_dict['locality'] = event_soup.find(class_='locality').get_text()
        else:
            temp_dict['locality'] = ''
        temp_dict['phone'] = event_soup.find(class_='owner').find_all('a', href=True)[0]['href'].replace('tel:','')
        temp_dict['email'] = event_soup.find(class_='owner').find_all('a', href=True)[1]['href'].replace('mailto:','')

        self.event_dicts.append(temp_dict)



    def getEvents(self):
        self.websiteNav()

        for event in self.events_html:
            self.extractEventInfo(event)
