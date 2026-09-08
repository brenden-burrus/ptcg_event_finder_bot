# import nodriver as uc
import zendriver as uc
import asyncio
import re
import time
import bs4
import datetime
import os


DATE_FORMAT = "%B %d %Y"


def tournament_date(tournament):
    """The day a tournament happens, read out of the date the locator renders.

    The locator gives a date as 'Friday, September 18, 2026'. Sorting those
    strings sorts by weekday name, which is how a Month Post came to list the
    18th before the 21st before the 12th -- #19. Anything that needs the
    tournaments in order asks here instead.

    Only the month, day and year are read, and commas are not required. The
    parse this replaced picked those three out by position, so it did not care
    what the weekday looked like or what followed the year; a renderer this
    project does not control gets the same latitude here.
    """
    month, day, year = tournament['date'].replace(",", " ").split()[1:4]
    return datetime.datetime.strptime(f"{month} {day} {year}", DATE_FORMAT)


def upcoming_tournaments(tournaments):
    """Keep only the tournaments still to come.

    A standalone function rather than a method because retained tournament
    data -- kept when a scrape fails -- has to be filtered the same way, and
    it no longer belongs to the finder that scraped it.

    Today counts as still to come. The scraped date carries no start time, so
    a tournament today could as easily be this evening as this morning, and
    hiding one a player could still get to is the worse of the two mistakes.
    """
    today = datetime.date.today()
    return [tournament for tournament in tournaments
            if tournament_date(tournament).date() >= today]


class PokemonEventFinder:
    def __init__(self, event_finder_url, search_location) -> None:
        self.url = event_finder_url
        self.search_location = search_location
        self.cup_dicts = []
        self.challenge_dicts = []

    
    def describeEmptyResults(self, page_source):
        # The results page reports its own count, which is what tells a
        # genuinely empty search apart from a selector that has gone stale.
        count = re.search(r'(\d+) Play! Pok\S*mon locations found', page_source)
        if not count:
            return "no stores found, and the results count could not be read -- the page layout may have changed"
        if count.group(1) == '0':
            return "no stores found: the search returned 0 locations"
        return f"no stores found, but the search reported {count.group(1)} locations -- the 'Game Store' selector may be stale"


    async def getEventSearchResults(self):
        # Start the browser and navigate to url. Starting it sits outside the
        # guarded region below: if starting is what fails there is no browser
        # to close, and the failure should propagate untouched.
        browser = await uc.start()
        try:
            page = await browser.get(self.url)
            await browser.wait(5)

            # Enter the search location into the text box and search
            consent = await page.find("Accept All", best_match=True)
            await consent.click()
            await browser.wait(3)
            test_input = await page.select("#b3-Input_LocationName")
            await test_input.send_keys(self.search_location)
            await browser.wait(3)
            dropdown_option = await page.select('.pac-item')
            await dropdown_option.mouse_click()
            await browser.wait(2)
            search_button = await page.find("Search Locations")
            await search_button.click()
            await browser.wait(5)

            # Iterate through all stores found in search results and parse its events
            try:
                store_list = await page.find_all('Game Store')
            except asyncio.TimeoutError:
                # zendriver raises instead of returning an empty list when the text
                # never appears, but matching no stores is a normal outcome -- an
                # off-season week with no Cups or Challenges scheduled, say. Only
                # the initial search gets this treatment: a timeout later in the
                # loop means the page stopped re-rendering, which is a real error.
                store_list = []
                print(self.describeEmptyResults(await page.get_content()))
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
        except BaseException:
            # A scrape that fails part-way still closes the browser on its way
            # out -- #21. Left open, zendriver's atexit fallback stops it while
            # the event loop is already being torn down, and the shut-down
            # executor it hits is the last thing printed instead of the real
            # failure.
            try:
                await browser.stop()
            except BaseException as close_failure:
                # Never let this replace the exception already in flight: a
                # browser that has died takes the interesting error with it.
                # BaseException rather than Exception because stopping waits on
                # the browser process, so the await can be cancelled -- and a
                # CancelledError caught here would be the one case that still
                # hid the real error.
                print(f"the browser could not be closed: {close_failure!r}")
            raise

        # On the success path a failure to close is the only failure there is,
        # so it propagates like any other.
        await browser.stop()

        return


    def parseStorePage(self, page_source, page_url):
        soup = bs4.BeautifulSoup(page_source, 'lxml')
        store_name_el = soup.find('span', attrs={'aria-label': lambda v: v and v.startswith('Game Store:')})
        if not store_name_el:
            # Some pages reached from the results list carry no store name.
            # Skipping just this page keeps the stores already parsed in this
            # run, rather than letting one odd page throw all of them away.
            print("no store name")
            return
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
        self.challenge_dicts = upcoming_tournaments(self.challenge_dicts)
        self.cup_dicts = upcoming_tournaments(self.cup_dicts)

        return


    def getEvents(self):
        asyncio.run(self.getEventSearchResults())
        self.CleanupPastEvents()

        
