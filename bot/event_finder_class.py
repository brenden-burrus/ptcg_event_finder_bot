# Contains the class that handles getting scrapted data from the Pokemon Event Finder

import time
import bs4
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class PokemonEventFinder:
    def __init__(self, url) -> None:
        self.url = url
        self.events_html = []
        self.event_dicts = []
        self.store_xref = {
            "Yeti Gaming": "84 GRASSO PLAZA, AFFTON, MO 63123, USA",
            "Grapes Games": "16431 VILLAGE PLAZA VIEW DR, WILDWOOD, MO 63011, USA",
            "Collector Store": "1106 JUNGS STATION RD",
            "Manticore Game Shop": "258 FORT ZUMWALT SQUARE",
            "Game Euphoria": "316 JEFFERSON ST",
            "Heroic Adventures": "1005 CENTURY DR",
            "Gambrill Gaming": "189 N LINCOLN DR",
            "Fortuna Games": "2632 S KINGSHIGHWAY BLVD",
            "Miniature Market - Cave Springs": "1077 CAVE SPRINGS BLVD",
            "Fantasy Books and Games": "1977 W HWY 50",
            "The Nerd Merchant": "124 West Jefferson Avenue, Unit 107"
        }

    
    def websiteNav(self):
        print('navigating website')
        self.events_html = []
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        driver.get(self.url)
        time.sleep(5)
        wait = WebDriverWait(driver, 10)
        button_list = driver.find_elements(By.CLASS_NAME, "event-card")
        print(f"initial: {len(button_list)}")
        for i in range(len(button_list)):
            buttons = driver.find_elements(By.CLASS_NAME, "event-card")
            print(f"i: {i}, len: {len(buttons)}")
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "event-card")))
            try:
                buttons[i].click()
                time.sleep(3)
                self.getEventHTML(driver.page_source)
                driver.back()
                time.sleep(3)
            except:
                pass
            

        driver.quit()
        print('done navigating')
        if len(self.events_html) != len(button_list):
            print(f"There are {len(self.events_html)} HTML records, and an initial button count of {len(button_list)}. Retrying")
            self.websiteNav()


    def getEventHTML(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        league = soup.find(id='league-detail-view')
        self.events_html.append(league)

    
    def getStoreName(self, soup_address):
        for store, address in self.store_xref.items():
            print(f"Comparing HTML: {soup_address} to dict: {address}")
            if address == soup_address:
                return store
            
        return None


    def extractEventInfo(self, event_soup):
        temp_dict = {}

        if event_soup.find(class_='when') == None:
            print(event_soup)
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
        temp_dict["store"] = self.getStoreName(temp_dict['address'])

        self.event_dicts.append(temp_dict)




    def getEvents(self):
        self.websiteNav()

        print("about to parse data")
        for event in self.events_html:
            self.extractEventInfo(event)

