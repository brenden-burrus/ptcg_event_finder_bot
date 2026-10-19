# import nodriver as uc
import zendriver as uc
import asyncio
import re
import time
import bs4
import datetime
import enum
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

    Today counts as still to come, all day. The scraped date carries a start
    time (#26), but it is only displayed: a tournament could still be running
    after it, or a player could still get to it, and hiding one they could
    still attend is the worse of the two mistakes. Hiding a tournament once it
    has started would be a separate decision.
    """
    today = datetime.date.today()
    return [tournament for tournament in tournaments
            if tournament_date(tournament).date() >= today]


class StorePageResult(enum.Enum):
    """What reading one Store page came to, for the scrape's run-level check.

    One page without the Upcoming Events section costs only itself, but no
    named page having it fails the scrape -- #27. These are the three ways a
    page can come out, named so that rule reads plainly where it is applied.
    """
    # Skipped unread, as under #9. It says nothing about the section either
    # way, so it counts neither way.
    NO_STORE_NAME = enum.auto()
    # A named page without the section: most likely a layout change (#26).
    NO_UPCOMING_EVENTS_SECTION = enum.auto()
    # The section was there and was read. A quiet Store lands here too: its
    # section is there with nothing under it, which is the page reading
    # correctly.
    READ = enum.auto()


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
            # How each Store page came out, for the check after the loop -- #27.
            page_results = set()
            i = 0
            imax = len(store_list)
            # print(len(store_list))
            while i < imax:
                await store_list[i].click()
                await browser.wait(3)
                html = await page.get_content()
                page_url = page.url
                page_results.add(self.parseStorePage(html, page_url))
                await browser.wait(3)
                back_button = await page.find("Back to previous screen")
                await back_button.click()
                await browser.wait(3)

                store_list = await page.find_all('Game Store')
                i += 2

            # One page without the section costs only itself, but none of them
            # having it is a layout change, which once passed for a quiet week:
            # every Store parsed as empty and the handler kept the old
            # tournaments without a word -- #27. Raised inside the guarded
            # region, so the browser is still closed (#21). A search that found
            # no Stores parsed no pages, so it stays a quiet week (#8), and a
            # page with no Store name counts neither way (#9).
            if (StorePageResult.NO_UPCOMING_EVENTS_SECTION in page_results
                    and StorePageResult.READ not in page_results):
                raise RuntimeError("no Store page had an Upcoming Events section"
                                   " -- the Store page layout may have changed")
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


    def findUpcomingEventsSection(self, soup):
        # Found by what its heading says, not by its id. The locator numbers
        # its sections by position, and has renumbered them twice; the second
        # time, the id the scrape read moved onto the Store's contact details
        # -- #26. The heading is English because the search URL pins the
        # locale to en-US.
        for title in soup.find_all('div', class_='custom-section__header__title'):
            if title.get_text(strip=True) == "Upcoming Events":
                return title.find_parent('div', class_='custom-section')
        return None


    def parseStorePage(self, page_source, page_url):
        # Returns how the page came out, for the scrape's run-level check
        # (#27): see StorePageResult.
        soup = bs4.BeautifulSoup(page_source, 'lxml')
        store_name_el = soup.find('span', attrs={'aria-label': lambda v: v and v.startswith('Game Store:')})
        if not store_name_el:
            # Some pages reached from the results list carry no store name.
            # Skipping just this page keeps the stores already parsed in this
            # run, rather than letting one odd page throw all of them away.
            print("no store name")
            return StorePageResult.NO_STORE_NAME
        store_name = store_name_el.get_text()
        upcoming_events = self.findUpcomingEventsSection(soup)
        if not upcoming_events:
            # Taken as not a quiet Store: a quiet one is expected to keep the
            # heading with nothing under it. Every Store page seen so far has
            # had the heading, but none of them was quiet -- #26. Skipping just
            # this page keeps the rest of the run, as for an unnamed page, but
            # the message says what it most likely means.
            print(f"{store_name}: no Upcoming Events section -- the Store page layout may have changed")
            return StorePageResult.NO_UPCOMING_EVENTS_SECTION
        # One event-info block is one tournament. The wrapper around each one
        # is no use: the Calendar widget in the same section shares it, and
        # has no tournament type to read -- #26. Only the section's own list,
        # directly under its content, is searched: the Calendar is a section
        # of its own beside that list, and nothing it ever holds is to be read
        # as an upcoming tournament. The list is found by the data-list mark
        # the locator puts on it, not by an id, which is numbered by position,
        # nor by its class, which the locator renders with stray quotes in it.
        event_cards = upcoming_events.select(':scope > div > [data-list] div.event-info')
        if not event_cards:
            # A quiet Store: the section is there and lists nothing. A normal
            # week for plenty of Stores, so it is said plainly.
            print(f"{store_name}: no upcoming tournaments")
            return StorePageResult.READ

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

        return StorePageResult.READ


    def CleanupPastEvents(self):
        self.challenge_dicts = upcoming_tournaments(self.challenge_dicts)
        self.cup_dicts = upcoming_tournaments(self.cup_dicts)

        return


    def getEvents(self):
        asyncio.run(self.getEventSearchResults())
        self.CleanupPastEvents()

        
