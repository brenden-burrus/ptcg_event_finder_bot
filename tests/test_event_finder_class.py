import asyncio

import pytest

import event_finder_class
from event_finder_class import PokemonEventFinder

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
    """

    def __init__(self, store_batches, content=EMPTY_RESULTS_PAGE):
        self.store_batches = list(store_batches)
        self.content = content
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
        return self.content


class FakeBrowser:
    def __init__(self, page):
        self.page = page
        self.stopped = False

    async def get(self, url):
        return self.page

    async def wait(self, seconds):
        return

    async def stop(self):
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


# --- #6: the location constructor argument drives the search -----------------


async def test_search_location_is_typed_into_the_box(fake_browser):
    page = FakePage([timed_out()])
    fake_browser(page)
    finder = PokemonEventFinder(URL, "Chicago, IL, USA")

    await finder.getEventSearchResults()

    assert page.location_input.typed == ["Chicago, IL, USA"]
