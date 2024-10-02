# Contains the class that handles getting scrapted data from the Pokemon Event Finder

import time
import bs4
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
import undetected_chromedriver as uc

class PokemonEventFinder:
    def __init__(self, url) -> None:
        self.url = url
        self.events_html = []
        self.event_dicts = []
        self.league_details = []
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
        self.store_urls = [
            "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/6238850/"
        ]

    
    def leagueDetailsNav(self, ttype):
        print('navigating league details page')

        #initializing webdriver

        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.removeScriptToEvaluateOnNewDocument", {"identifier":"1"})
        time.sleep(3)
        # driver.get("https://sslproxies.org/")
        # driver.execute_script("return arguments[0].scrollIntoView(true);", WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//table[@class='table table-striped table-bordered']//th[contains(., 'IP Address')]"))))
        # ips = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 1]")))]
        # ports = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located((By.XPATH, "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 2]")))]
        # driver.quit()
        # proxies = []
        # for i in range(0, len(ips)):
        #     proxies.append(ips[i]+':'+ports[i])
        # print(proxies)
        # for i in range(0, len(proxies)):
        #     try:
        #         print("Proxy selected: {}".format(proxies[i]))
        #         options = webdriver.ChromeOptions()
        #         options.add_argument('--proxy-server={}'.format(proxies[i]))
        #         driver = webdriver.Chrome(options=options, executable_path=r'C:\WebDrivers\chromedriver.exe')
        #         driver.get("https://www.whatismyip.com/proxy-check/?iref=home")
        #         if "Proxy Type" in WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "p.card-text"))):
        #             break
        #     except Exception:
        #         driver.quit()
        # print("Proxy Invoked")

        wait = WebDriverWait(driver, 10)

        #Hide webdriver
        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value]
        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
        user_agent = user_agent_rotator.get_random_user_agent()
        stealth(
            driver,
            user_agent= user_agent,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

        for league_url in self.store_urls:
            driver.get(league_url)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "left-content")))
            temp_league_details = self.getLeagueHTML(driver.page_source)
            time.sleep(3)
            driver.get(league_url + ttype)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "pane")))
            temp_tourney_details = self.getTourneyHTML(driver.page_source)
            time.sleep(3)
            print({temp_league_details: temp_tourney_details})
            self.league_details.append({temp_league_details: temp_tourney_details})
        print("done getting league details")



    def websiteNav(self):
        print('navigating website')
        self.events_html = []
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)

        #Hide webdriver
        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value]
        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
        user_agent = user_agent_rotator.get_random_user_agent()
        stealth(
            driver,
            user_agent= user_agent,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
        
        driver.get(self.url)
        time.sleep(5)
        wait = WebDriverWait(driver, 10)
        button_list = driver.find_elements(By.CLASS_NAME, "event-card")
        button_amt = len(button_list)
        print(f"initial: {button_amt}")
        for i in range(button_amt):
            buttons = driver.find_elements(By.CLASS_NAME, "event-card")
            print(f"i: {i}, len: {button_amt}")
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "event-card")))
            try:
                buttons[i].click()
                time.sleep(3)
                self.getEventHTML(driver.page_source)
                details = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="league-detail-view"]/div[2]/div[3]/a')))
                self.league_details.append(details.get_attribute('href'))
                time.sleep(3)
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

    
    def getLeagueHTML(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        league = soup.find(id='left-content')
        return league
    

    def getTourneyHTML(self, html):
        soup = bs4.BeautifulSoup(html, 'lxml')
        tourney_details = soup.find('table')
        return tourney_details

    
    def getStoreName(self, soup_address):
        for store, address in self.store_xref.items():
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
        temp_dict['month'] = temp_dict['when'].split(' ')[0]
        temp_dict['year'] = temp_dict['when'].split(' ')[2]

        self.event_dicts.append(temp_dict)




    def getEvents(self, type):
        # self.websiteNav()

        # print("navigating to league details site")
        # for site_url in self.league_details:
        #     self.leagueSiteNav(site_url, type)

        # print("about to parse data")
        # for event in self.events_html:
        #     self.extractEventInfo(event)

        self.leagueDetailsNav(type)
