import asyncio
import datetime
import warnings

import pytest

import event_finder_class
from event_finder_class import (
    PokemonEventFinder,
    tournament_date,
    upcoming_tournaments,
)

URL = "https://events.pokemon.com/EventLocator/Home?filters=league_cup,league_challenge,tcg"
LOCATION = "St. Louis, MO, USA"

EMPTY_RESULTS_PAGE = '<div class="results">0 Play! Pokémon locations found</div>'


class FakeElement:
    """Stands in for a zendriver element. Records what was typed into it."""

    def __init__(self):
        self.typed = []

    async def click(self):
        return

    async def mouse_click(self):
        return

    async def send_keys(self, text):
        self.typed.append(text)


class FakePage:
    """Stands in for a zendriver tab.

    `store_batches` is the sequence of results `find_all` hands back on
    successive calls; a batch may be an exception instance, which is raised
    instead. zendriver's real `find_all` raises `asyncio.TimeoutError` when the
    text never appears, rather than returning an empty list.

    `content` is the page source `get_content` returns. Pass a list to serve a
    different source on each call, one per store the loop visits; the last one
    sticks once the list runs down.
    """

    def __init__(self, store_batches, content=EMPTY_RESULTS_PAGE):
        self.store_batches = list(store_batches)
        self.page_sources = list(content) if isinstance(content, list) else [content]
        self.url = "https://events.pokemon.com/EventLocator/Store/1"
        self.location_input = FakeElement()

    async def find(self, text, best_match=False):
        return FakeElement()

    async def select(self, selector):
        if selector == "#b3-Input_LocationName":
            return self.location_input
        return FakeElement()

    async def find_all(self, text):
        batch = self.store_batches.pop(0) if self.store_batches else []
        if isinstance(batch, BaseException):
            raise batch
        return batch

    async def get_content(self):
        if len(self.page_sources) > 1:
            return self.page_sources.pop(0)
        return self.page_sources[0]


class FakeBrowser:
    def __init__(self, page):
        self.page = page
        self.stopped = False
        self.loop = None

    async def get(self, url):
        return self.page

    async def wait(self, seconds):
        return

    async def stop(self):
        # Recorded so a test can ask what happened to the loop the scrape ran
        # on, once the synchronous entry point has returned.
        self.loop = asyncio.get_running_loop()
        self.stopped = True


@pytest.fixture
def fake_browser(monkeypatch):
    """Swap zendriver's `start` for a fake, and hand the browser back."""

    def _install(page):
        browser = FakeBrowser(page)

        async def fake_start():
            return browser

        monkeypatch.setattr(event_finder_class.uc, "start", fake_start)
        return browser

    return _install


def timed_out():
    return asyncio.TimeoutError("time ran out while waiting for text: Game Store")


def tournament_on(year, month, day, name="League Cup"):
    """A tournament carrying the date string the event locator renders.

    The weekday is derived rather than written out, so a test states the date
    it means and cannot accidentally pair it with the wrong day name -- which
    is exactly the pairing #19 is about.
    """
    when = datetime.date(year, month, day)
    return {'date': f"{when.strftime('%A')}, {when.strftime('%B')} {day}, {year}",
            'name': name}


# --- #8: an empty search is not an error -------------------------------------


async def test_no_stores_found_yields_empty_results(fake_browser):
    """A search that legitimately matches zero stores is not an error.

    Regression test for #8: `find_all` raised straight out of the scrape, so an
    off-season week with no Cups or Challenges crashed the scheduled job
    instead of simply reporting nothing.
    """
    page = FakePage([timed_out()])
    browser = fake_browser(page)
    finder = PokemonEventFinder(URL, LOCATION)

    await finder.getEventSearchResults()

    assert finder.cup_dicts == []
    assert finder.challenge_dicts == []
    assert browser.stopped, "browser must be closed even when nothing is found"


def test_getEvents_returns_cleanly_when_nothing_is_found(fake_browser):
    """The whole synchronous entry point must survive an empty search.

    This is the path `getLocalEvents()` actually calls, so it is what decides
    whether the scheduled job crashes or posts nothing.
    """
    fake_browser(FakePage([timed_out()]))
    finder = PokemonEventFinder(URL, LOCATION)

    finder.getEvents()

    assert finder.cup_dicts == []
    assert finder.challenge_dicts == []


async def test_empty_search_is_logged(fake_browser, capsys):
    """#8 asks for the empty case to be visible, not silent."""
    fake_browser(FakePage([timed_out()]))
    finder = PokemonEventFinder(URL, LOCATION)

    await finder.getEventSearchResults()

    assert "no stores found" in capsys.readouterr().out


async def test_stores_found_are_still_parsed(fake_browser):
    """The empty-result handling must not swallow real results."""
    page = FakePage([[FakeElement(), FakeElement()], []])
    browser = fake_browser(page)
    finder = PokemonEventFinder(URL, LOCATION)

    parsed = []
    finder.parseStorePage = lambda html, url: parsed.append(url)

    await finder.getEventSearchResults()

    assert parsed == ["https://events.pokemon.com/EventLocator/Store/1"]
    assert browser.stopped


async def test_timeout_after_the_first_store_still_raises(fake_browser):
    """Only the initial search is allowed to come back empty.

    Once a store has been clicked into we know the list existed, so a later
    timeout means the page stopped re-rendering -- a real failure that must not
    be silently reported as a complete, shorter run.
    """
    page = FakePage([[FakeElement(), FakeElement()], timed_out()])
    fake_browser(page)
    finder = PokemonEventFinder(URL, LOCATION)
    finder.parseStorePage = lambda html, url: None

    with pytest.raises(asyncio.TimeoutError):
        await finder.getEventSearchResults()


# --- #8: telling an empty week apart from a stale selector -------------------


def test_zero_locations_reads_as_a_genuinely_empty_search():
    finder = PokemonEventFinder(URL, LOCATION)

    message = finder.describeEmptyResults(EMPTY_RESULTS_PAGE)

    assert message == "no stores found: the search returned 0 locations"


def test_locations_without_stores_reads_as_a_stale_selector():
    finder = PokemonEventFinder(URL, LOCATION)

    message = finder.describeEmptyResults("<div>31 Play! Pokémon locations found</div>")

    assert "31 locations" in message
    assert "stale" in message


def test_unreadable_results_count_is_called_out():
    finder = PokemonEventFinder(URL, LOCATION)

    message = finder.describeEmptyResults("<div>something else entirely</div>")

    assert "could not be read" in message


# --- parsing a store page (and the lxml parser it needs) ---------------------


STORE_PAGE = """
<html><body>
  <span aria-label="Game Store: FORTUNA GAMES">FORTUNA GAMES</span>
  <div id="b11-Content">
    <div class="margin-bottom-base">
      <div class="event-info__category ph">Cup</div>
      <div class="event-info__title ph">League Cup</div>
      <div class="event-info__info-item__location">123 Main St</div>
      <div class="event-info__info-item__text">Saturday, September 12, 2026</div>
    </div>
    <div class="margin-bottom-base">
      <div class="event-info__category ph">Challenge</div>
      <div class="event-info__title ph">League Challenge</div>
      <div class="event-info__info-item__location">123 Main St</div>
      <div class="event-info__info-item__text">Sunday, September 13, 2026</div>
    </div>
  </div>
</body></html>
"""


def test_store_page_events_are_split_by_category():
    """Also pins the lxml dependency.

    `parseStorePage` asks BeautifulSoup for the 'lxml' parser explicitly, so a
    missing lxml fails here with bs4.FeatureNotFound rather than part-way
    through a live scrape.
    """
    finder = PokemonEventFinder(URL, LOCATION)

    finder.parseStorePage(STORE_PAGE, "https://events.pokemon.com/EventLocator/Store/1")

    assert [event['name'] for event in finder.cup_dicts] == ["League Cup"]
    assert [event['name'] for event in finder.challenge_dicts] == ["League Challenge"]
    # The element is located by its aria-label, but the store name comes from
    # the element's text, so the "Game Store: " prefix is not part of it.
    assert finder.cup_dicts[0]['store'] == "FORTUNA GAMES"
    assert finder.cup_dicts[0]['tourney_address'] == "123 Main St"


# --- #9: a page without a store name must not sink the whole run -------------


PAGE_WITHOUT_A_STORE_NAME = """
<html><body>
  <div id="b11-Content">
    <div class="margin-bottom-base">
      <div class="event-info__category ph">Cup</div>
      <div class="event-info__title ph">League Cup</div>
      <div class="event-info__info-item__location">123 Main St</div>
      <div class="event-info__info-item__text">Saturday, September 12, 2026</div>
    </div>
  </div>
</body></html>
"""


def test_page_without_a_store_name_is_skipped(capsys):
    """Regression test for #9.

    Some pages reached from the results list carry no 'Game Store:' span. The
    lookup used to be unguarded, so one such page raised AttributeError.
    """
    finder = PokemonEventFinder(URL, LOCATION)

    finder.parseStorePage(PAGE_WITHOUT_A_STORE_NAME, "https://events.pokemon.com/EventLocator/Store/7")

    assert finder.cup_dicts == []
    assert finder.challenge_dicts == []
    assert "no store name" in capsys.readouterr().out


async def test_one_unnamed_store_does_not_discard_the_rest_of_the_run(fake_browser):
    """The crash in #9 happened mid-iteration, so it cost every earlier store.

    The run must keep the store it has already parsed, carry on past the
    unnamed one, and still close the browser.
    """
    # Each store contributes two 'Game Store' matches, hence the stride of two
    # in the loop: four elements is two stores. The named store is visited
    # first, so its events are already banked when the unnamed one comes up --
    # the sequence the issue reported.
    stores = [FakeElement() for _ in range(4)]
    page = FakePage([stores, stores, stores], content=[STORE_PAGE, PAGE_WITHOUT_A_STORE_NAME])
    browser = fake_browser(page)
    finder = PokemonEventFinder(URL, LOCATION)

    await finder.getEventSearchResults()

    assert [event['store'] for event in finder.cup_dicts] == ["FORTUNA GAMES"]
    assert browser.stopped


# --- #6: the location constructor argument drives the search -----------------


async def test_search_location_is_typed_into_the_box(fake_browser):
    page = FakePage([timed_out()])
    fake_browser(page)
    finder = PokemonEventFinder(URL, "Chicago, IL, USA")

    await finder.getEventSearchResults()

    assert page.location_input.typed == ["Chicago, IL, USA"]


# --- #12: the synchronous entry point runs on a supported event loop ---------


def test_getEvents_calls_nothing_deprecated(fake_browser):
    """Regression test for #12.

    `getEvents` drove the scrape with `uc.loop()`, deprecated in zendriver
    since 0.5.1 and still called on 0.16.0. It is the only entry point the
    scheduled job has, so losing it on an upgrade stops the whole job.

    Scoped to warnings blamed on this project's own module: a deprecation
    inside bs4 or the stdlib is not this test's business, and would otherwise
    fail it for something no one here can fix.
    """
    fake_browser(FakePage([timed_out()]))
    finder = PokemonEventFinder(URL, LOCATION)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        finder.getEvents()

    ours = [
        w for w in caught
        if issubclass(w.category, DeprecationWarning)
        and w.filename.endswith("event_finder_class.py")
    ]
    assert not ours, f"deprecated call: {[str(w.message) for w in ours]}"


# --- #19: reading the day a tournament happens -------------------------------


def test_the_rendered_date_reads_back_as_the_day_it_happens():
    assert tournament_date(tournament_on(2026, 9, 18)) == datetime.datetime(2026, 9, 18)


def test_a_zero_padded_day_reads_the_same():
    """The locator is a remote renderer this project does not control.

    Nothing observed pads the day, but a padded one must not crash a scrape
    that would otherwise have worked.
    """
    padded = {'date': "Saturday, September 05, 2026"}

    assert tournament_date(padded) == datetime.datetime(2026, 9, 5)


def test_anything_after_the_year_is_ignored():
    """The parse this replaced took the date apart by position and ignored the
    rest of the string, so a multi-day or timed date still worked. Keeping that
    tolerance means a format the locator has never shown us cannot take the
    nightly scrape down.
    """
    spanning = {'date': "Saturday, September 12, 2026 - Sunday, September 13, 2026"}

    assert tournament_date(spanning) == datetime.datetime(2026, 9, 12)


# --- #19: tournaments post in the order they happen --------------------------


SEPTEMBER_2026_DAYS = [18, 21, 12, 26, 26, 26, 26, 26, 20, 27, 27, 10, 17, 24, 16]


def test_tournaments_sort_into_the_order_they_happen():
    """Regression test for #19.

    Ordering came from sorting the rendered date string, so 'Friday, September
    18' sorted before 'Monday, September 21' before 'Saturday, September 12':
    by weekday name. These are the September tournaments as they posted on
    2026-09-07, in the order the bug put them in.
    """
    tournaments = [tournament_on(2026, 9, day) for day in SEPTEMBER_2026_DAYS]

    ordered = sorted(tournaments, key=tournament_date)

    assert [tournament_date(t).day for t in ordered] == sorted(SEPTEMBER_2026_DAYS)


def test_a_year_boundary_orders_by_date_not_by_month_name():
    """December must precede January when January is the following year.

    Sorting on anything drawn from the rendered string puts April first and
    January second; only the date gets this right.
    """
    december = tournament_on(2026, 12, 30)
    january = tournament_on(2027, 1, 3)
    april = tournament_on(2027, 4, 1)

    ordered = sorted([april, january, december], key=tournament_date)

    assert ordered == [december, january, april]


def test_two_tiers_interleave_by_date():
    """A general channel concatenated two separately ordered lists, so every
    League Challenge preceded every League Cup whatever its date -- #19.
    """
    cups = [tournament_on(2026, 9, 12, name="League Cup"),
            tournament_on(2026, 9, 26, name="League Cup")]
    challenges = [tournament_on(2026, 9, 10, name="League Challenge"),
                  tournament_on(2026, 9, 20, name="League Challenge")]

    ordered = sorted(challenges + cups, key=tournament_date)

    assert [(tournament_date(t).day, t['name']) for t in ordered] == [
        (10, "League Challenge"),
        (12, "League Cup"),
        (20, "League Challenge"),
        (26, "League Cup"),
    ]


# --- #19: the past-tournament filter, deferred here from #16 -----------------


def days_from_today(offset):
    when = datetime.date.today() + datetime.timedelta(days=offset)
    return tournament_on(when.year, when.month, when.day)


def test_a_tournament_still_to_come_is_kept():
    tournament = days_from_today(3)

    assert upcoming_tournaments([tournament]) == [tournament]


def test_a_tournament_that_has_happened_is_dropped():
    assert upcoming_tournaments([days_from_today(-3)]) == []


def test_a_tournament_falling_today_is_dropped():
    """Pins today's behaviour rather than endorsing it.

    The filter compares midnight on the tournament's day against the moment it
    runs, so a tournament happening today reads as past from 00:00 onwards.
    The scraped data carries no start time, so the bot cannot tell a tournament
    that has finished from one starting this evening; dropping both is the
    current answer. Changing it is a product decision, not a refactor.
    """
    assert upcoming_tournaments([days_from_today(0)]) == []


def test_the_order_tournaments_arrived_in_is_preserved():
    """The filter is not a sort. Callers order the result themselves, and a
    filter that quietly reordered would hide whether they did.
    """
    later, sooner = days_from_today(9), days_from_today(2)

    assert upcoming_tournaments([later, sooner]) == [later, sooner]


def test_filtering_leaves_the_list_it_was_given_alone():
    """Callers rebind their list to the result; retention (#18) reruns the
    filter over the stored tournaments, so a filter that mutated in place
    would be filtering the caller's data out from under it.
    """
    tournaments = [days_from_today(-3), days_from_today(3)]

    upcoming_tournaments(tournaments)

    assert len(tournaments) == 2


def test_an_empty_list_filters_to_an_empty_list():
    assert upcoming_tournaments([]) == []


def test_the_finder_filters_both_tiers():
    """`CleanupPastEvents` delegates twice, once per tier. #16 asked for the
    duplicated filter to go; this is what stops one tier being reconnected and
    the other forgotten.
    """
    past, upcoming = days_from_today(-4), days_from_today(4)
    finder = PokemonEventFinder(URL, LOCATION)
    finder.cup_dicts = [past, upcoming]
    finder.challenge_dicts = [upcoming, past]

    finder.CleanupPastEvents()

    assert finder.cup_dicts == [upcoming]
    assert finder.challenge_dicts == [upcoming]


def test_getEvents_closes_the_loop_it_opened(fake_browser):
    """`uc.loop()` handed back a loop that `run_until_complete` never closed.

    The scheduled job calls `getEvents` once a night for the life of the
    process, so each run leaked a loop. Asking the browser which loop it was
    stopped on pins the loop the scrape actually used, rather than whatever
    happens to be installed on this thread once the suite has run.
    """
    browser = fake_browser(FakePage([timed_out()]))
    finder = PokemonEventFinder(URL, LOCATION)

    finder.getEvents()

    assert browser.loop is not None, "the scrape never ran"
    assert browser.loop.is_closed(), "the loop getEvents opened was left open"
