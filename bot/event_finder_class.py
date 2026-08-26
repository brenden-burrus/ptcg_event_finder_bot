# import nodriver as uc
import zendriver as uc
import time
import bs4
import datetime
import calendar
import os


class PokemonEventFinder:
    def __init__(self, event_finder_url) -> None:
        self.url = event_finder_url
        self.cup_dicts = []
        self.challenge_dicts = []

    
    async def getEventSearchResults(self):
        # Start the broswer and navigate to url
        browser = await uc.start()
        page = await browser.get(self.url)
        await browser.wait(5)

        # Enter STL into the text box and search
        consent = await page.find("Accept All", best_match=True)
        await consent.click()
        await browser.wait(3)
        test_input = await page.select("#b3-Input_LocationName")
        await test_input.send_keys("St. Louis, MO, USA")
        await browser.wait(3)
        dropdown_option = await page.select('.pac-item')
        await dropdown_option.mouse_click()
        await browser.wait(2)
        search_button = await page.find("Search Locations")
        await search_button.click()
        await browser.wait(5)
        
        # Iterate through all stores found in search results and parse its events
        store_list = await page.find_all('Game Store')
        i = 0
        imax = len(store_list)
        # print(len(store_list))
        while i < imax:
            await store_list[i].click()
            await browser.wait(3)
            html = await page.get_content()
            page_url = page.url
            self.parseStorePage(html, page_url)
            await browser.wait(3)
            back_button = await page.find("Back to previous screen")
            await back_button.click()
            await browser.wait(3)
            
            store_list = await page.find_all('Game Store')
            i += 2

        await browser.stop()

        return


    def parseStorePage(self, page_source, page_url):
        soup = bs4.BeautifulSoup(page_source, 'lxml')
        store_name_el = soup.find('span', attrs={'aria-label': lambda v: v and v.startswith('Game Store:')})
        store_name = store_name_el.get_text()
        cards_list = soup.find('div', id='b11-Content')
        if not cards_list:
            print("no cards")
            return
        event_cards = cards_list.find_all('div', class_='margin-bottom-base')
        if not event_cards:
            print("no event cards")
            return

        print(f"{store_name}")
        for card in event_cards:
            temp_dict = {}
            tourney_type = card.find('div', class_='event-info__category ph').get_text()
            tourney_name = card.find('div', class_='event-info__title ph').get_text()
            address = card.find('div', class_='event-info__info-item__location').get_text()
            date = card.find('div', class_='event-info__info-item__text').get_text()
 
            temp_dict['store'] = store_name
            temp_dict['name'] = tourney_name
            temp_dict['date'] = date
            temp_dict['tourney_page'] = page_url
            temp_dict['tourney_address'] = address
            # print(temp_dict)
            if tourney_type == "Cup":
                self.cup_dicts.append(temp_dict)
            else:
                self.challenge_dicts.append(temp_dict)

        return


    def CleanupPastEvents(self):
        today = datetime.datetime.now()
        temp_list = []
        for i in range(len(self.challenge_dicts)):
            month = self.challenge_dicts[i]['date'].split(" ")[1]
            year = int(self.challenge_dicts[i]['date'].split(" ")[3])
            day = int(self.challenge_dicts[i]['date'].split(" ")[2].replace(',',''))

            for y in range(len(calendar.month_name)):
                if str(calendar.month_name[y]) == str(month):
                    month = y
                    break

            if datetime.datetime(year, month, day) > today:
                temp_list.append(self.challenge_dicts[i])

        self.challenge_dicts = temp_list

        temp_list = []
        for i in range(len(self.cup_dicts)):
            month = self.cup_dicts[i]['date'].split(" ")[1]
            year = int(self.cup_dicts[i]['date'].split(" ")[3])
            day = int(self.cup_dicts[i]['date'].split(" ")[2].replace(',',''))

            for y in range(len(calendar.month_name)):
                if str(calendar.month_name[y]) == str(month):
                    month = y
                    break

            if datetime.datetime(year, month, day) > today:
                temp_list.append(self.cup_dicts[i])

        self.cup_dicts = temp_list
        
        return




    def getEvents(self):
        uc.loop().run_until_complete(self.getEventSearchResults())
        self.CleanupPastEvents()

        
