import nodriver as uc
import time
import bs4
import datetime
import calendar


class PokemonEventFinder:
    def __init__(self, event_finder_url) -> None:
        self.url = event_finder_url
        self.league_table_dicts = []
        self.event_finder_dicts = []
        self.event_dicts = []
        self.store_urls = {
            "Yeti Gaming": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/4719/",
            "Grapes Games": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/6238850/",
            "Collector Store": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/4423201/",
            "Manticore Game Shop": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/108903/",
            "Game Euphoria": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/6234924/",
            "Heroic Adventures": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/3023200/",
            "Gambrill Gaming": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/6239029/",
            "Fortuna Games": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/6235772/",
            "Fantasy Books and Games": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/5863209/",
            "The Nerd Merchant": "https://www.pokemon.com/us/play-pokemon/pokemon-events/leagues/6239453/"}
        self.store_xref = {
            "Yeti Gaming": "84 GRASSO PLAZA, AFFTON, MO 63123, USA",
            "Grapes Games": "16431 VILLAGE PLAZA VIEW DR, WILDWOOD, MO 63011, USA",
            "Collector Store": "1106 JUNGS STATION RD",
            "Manticore Game Shop": "258 FORT ZUMWALT SQUARE",
            "Game Euphoria": "316 JEFFERSON ST",
            "Heroic Adventures": "1005 CENTURY DR",
            "Gambrill Gaming": "189 N LINCOLN DR",
            "Fortuna Games": "2632 S KINGSHIGHWAY BLVD",
            "Fantasy Books and Games": "1977 W HWY 50",
            "The Nerd Merchant": "124 W JEFFERSON AVE STE 107"
        }

    # Gets the table for either cups or challenges from the store's page on pokemon.com
    async def getStoreEventTable(self, store, base_url, ttype):
        browser = await uc.start()
        page = await browser.get(base_url+ttype)
        await browser.wait(5)
        html = await page.get_content()
        self.parseTable(html, store)
        await browser.wait(5)
        browser.stop()

        return


    async def getEventFinderCards(self):
        browser = await uc.start()
        page = await browser.get(self.url)
        await browser.wait(5)
        card_amt = await page.select('#sort-control > div.count')
        card_amt = int(card_amt.text.split(' ')[0])
        card_list = []
        while len(card_list) < card_amt:
            html = await page.get_content()
            cards = self.parseEventList(html)
            card_list.extend(cards)
            card_list = list(set(card_list))
            card_holders = await page.find_all("card-holder")
            await card_holders[-1].scroll_into_view()
            await browser.wait(3)

        browser.stop()
        self.parseCards(card_list)

        return

    
    # Parses the table to get the wanted info from it
    def parseTable(self, page_source, store):
        soup = bs4.BeautifulSoup(page_source, 'lxml')
        table = soup.find('table')
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')

        for row in rows:
            temp_dict = {}
            link = row.find('a').get('href')
            link = "https://www.pokemon.com"+link
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            cols.append(link)
            if cols[2] == 'Sanctioned' and "TCG" in cols[0]:
                temp_dict['store'] = store
                temp_dict['name'] = cols[0]
                temp_dict['date'] = cols[3]
                temp_dict['tourney_page'] = cols[4]
                self.league_table_dicts.append(temp_dict)


    def parseEventList(self, page_source):
        soup = bs4.BeautifulSoup(page_source, 'lxml')
        cards = soup.find_all(class_='event-card')
        info_list = []

        for card in cards:
            address = card.find(class_='address').get_text().replace(" ", "_")
            name = card.find(class_='event-header').get_text().replace(" ", "_")
            date = card.find(class_='when').get_text().replace(" ", "_")
            temp_text = address + " " + name + " " + date + " "
            info_list.append(temp_text)

        return info_list



    def parseCards(self, card_list):
        print(f"There are {len(card_list)} event cards")

        for card in card_list:
            print(f"heres the card: {card}")
            address, name, date = card.split(' ', 2)
            address = address.replace('_', " ")
            name = name.replace('_', " ")
            date = date.replace('_', " ")
            time = date.split(" ")[-2]
            print(f"time - {time}")
            print(f"{address}, {name}, {date}")

            for store, xref in self.store_xref.items():
                if xref == address:
                    store_name = store
                    break

            for event in self.league_table_dicts:
                if event['store'] == store_name and event['date'] in date:
                    event['time'] = time
                    event['name'] = name
                    break
            

    def CleanupPastEvents(self):
        today = datetime.datetime.now()
        temp_list = []
        for i in range(len(self.league_table_dicts)):
            month = self.league_table_dicts[i]['date'].split(" ")[0]
            year = int(self.league_table_dicts[i]['date'].split(" ")[-1])
            day = int(self.league_table_dicts[i]['date'].split(" ")[1].replace(',',''))

            for y in range(len(calendar.month_name)):
                if str(calendar.month_name[y]) == str(month):
                    month = y
                    break

            if datetime.datetime(year, month, day) > today:
                temp_list.append(self.league_table_dicts[i])

        self.league_table_dicts = temp_list
        
        return




    def getEvents(self, ttype):
        for store, url in self.store_urls.items():
            uc.loop().run_until_complete(self.getStoreEventTable(store, url, ttype))

        uc.loop().run_until_complete(self.getEventFinderCards())
        self.CleanupPastEvents()

        
