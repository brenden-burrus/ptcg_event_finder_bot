"""Building the messages that make up a Month Post.

Regression tests for #17: a month with enough tournaments rendered past
Discord's 2000-character limit, so `ctx.send` raised and the whole command
produced nothing -- including for the months that would have fitted.
"""

import pytest

from bot_functions import DISCORD_MESSAGE_LIMIT, build_month_posts

TITLE = "September League Challenges"

# The fifteen September League Challenges as they rendered on 2026-09-07, by
# length. They sum to 2287, which with a header put the Month Post at 2320 --
# the message Discord rejected.
SEPTEMBER_2026_EVENT_LENGTHS = [
    163, 131, 169, 142, 148, 157, 138, 170, 149, 162, 130, 147, 137, 207, 137,
]


def event_of_length(index, length):
    """An identifiable event of an exact length, so packing can be checked."""
    marker = f"__{index}__"
    return marker + "x" * (length - len(marker) - 1) + "\n"


def events_of_length(count, length):
    return [event_of_length(i, length) for i in range(count)]


# --- #17: a month too big for one message is split, not dropped --------------


def test_a_month_that_fits_is_one_message():
    posts = build_month_posts(TITLE, ["a\n", "b\n"], limit=100)

    assert posts == ["# *September League Challenges*\n\na\nb\n"]


def test_a_month_that_does_not_fit_is_split():
    """Regression test for #17: this is the case that raised the 400.

    Three 30-character events cannot share a 100-character message.
    """
    posts = build_month_posts(TITLE, events_of_length(3, 30), limit=100)

    assert len(posts) > 1
    assert all(len(post) <= 100 for post in posts), [len(p) for p in posts]


def test_splitting_never_divides_an_event_or_drops_one():
    """The whole point of splitting on event boundaries.

    Each event is distinguishable, so a divided one shows up as a message
    containing part of its text, and a dropped one as a missing marker.
    """
    events = events_of_length(12, 33)

    posts = build_month_posts(TITLE, events, limit=150)

    joined = "".join(posts)
    for e in events:
        assert joined.count(e) == 1, f"event mangled or lost: {e!r}"


def test_a_month_filling_the_budget_exactly_stays_one_message():
    """Off-by-one at the boundary is how a limit bug survives its own fix."""
    posts = build_month_posts(TITLE, ["a" * 79, "b" * 79], limit=200)

    assert len(posts) == 1
    assert len(posts[0]) <= 200


def test_one_character_over_the_budget_splits():
    posts = build_month_posts(TITLE, ["a" * 79, "b" * 80], limit=200)

    assert len(posts) == 2
    assert all(len(post) <= 200 for post in posts), [len(p) for p in posts]


def test_an_empty_month_produces_no_messages():
    """A month with nothing in it must not post a lone header."""
    assert build_month_posts(TITLE, [], limit=100) == []


def test_a_limit_too_small_for_the_header_is_refused():
    """There is no honest answer, so say so rather than exceed the limit.

    Only reachable through the limit parameter the tests use; a caller
    hitting this has asked for something impossible.
    """
    with pytest.raises(ValueError):
        build_month_posts(TITLE, ["a\n"], limit=10)


# --- #17: numbering, and the invariant a Refresh depends on ------------------


def test_a_split_month_post_numbers_every_message():
    """A reader has to be able to tell a continued list from a truncated one."""
    posts = build_month_posts(TITLE, events_of_length(3, 30), limit=110)

    headers = [post.split("\n")[0] for post in posts]
    assert headers == [
        "# *September League Challenges (1 of 2)*",
        "# *September League Challenges (2 of 2)*",
    ]


def test_every_message_carries_its_month_on_the_first_line():
    """The invariant a Refresh depends on -- see ADR-0001.

    delete_old_messages matches a month name in the first line only, so a
    message of a Month Post that lacks one is never deleted and the next
    Refresh leaves a duplicate behind. Asserted here rather than inferred
    from the header format, because it is the header format's whole reason
    for existing.
    """
    posts = build_month_posts(TITLE, events_of_length(12, 33), limit=150)

    assert len(posts) > 1, "this test is pointless without a split"
    for post in posts:
        assert "September" in post.split("\n")[0], post.split("\n")[0]


# --- #17: an event that cannot fit alone -------------------------------------


def test_an_event_too_long_to_fit_alone_is_truncated_not_dropped():
    """No tournament disappears silently.

    Not reachable with today's data -- the longest event text observed is 207
    characters against a 2000 limit -- but dropping the event would hide a
    tournament from users, and letting it through would raise the same 400
    this whole change exists to stop.
    """
    events = ["short\n", "__big__" + "L" * 500 + "\n", "also short\n"]

    posts = build_month_posts(TITLE, events, limit=120)

    assert all(len(post) <= 120 for post in posts), [len(p) for p in posts]
    joined = "".join(posts)
    assert "short\n" in joined and "also short\n" in joined
    # Truncated rather than mangled: it keeps its opening and is marked as cut.
    assert "__big__LLL" in joined, "the oversized event was dropped or mangled"
    assert "...\n" in joined, "the truncation is not signalled to the reader"


def test_an_oversized_event_gets_a_message_to_itself():
    """It fills a whole message by construction, so nothing may share it."""
    events = ["short\n", "__big__" + "L" * 500 + "\n", "also short\n"]

    posts = build_month_posts(TITLE, events, limit=120)

    carrying_big = [post for post in posts if "__big__" in post]
    assert len(carrying_big) == 1
    assert "short\n" not in carrying_big[0], "another event shares its message"


# --- #17: the reported failure -----------------------------------------------


def test_the_september_2026_month_post_that_broke_the_command():
    """Regression test for #17, at the real limit rather than a test one."""
    events = [event_of_length(i, length)
              for i, length in enumerate(SEPTEMBER_2026_EVENT_LENGTHS)]
    assert sum(len(e) for e in events) == 2287, "sample no longer matches #17"

    posts = build_month_posts(TITLE, events)

    assert all(len(post) <= DISCORD_MESSAGE_LIMIT for post in posts), \
        [len(p) for p in posts]
    assert [post.count("__") // 2 for post in posts] == [13, 2]
    assert all("September" in post.split("\n")[0] for post in posts)
