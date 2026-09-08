# PTCG Event Finder

A Discord bot that scrapes Play! Pokémon's public event locator for organised-play
tournaments near a search location, and posts them into Discord channels on request.

## Language

### Tournaments

**League Cup**:
A Play! Pokémon organised-play tournament of the Cup tier, held at a Store.
_Avoid_: Cup event, tourney

**League Challenge**:
A Play! Pokémon organised-play tournament of the Challenge tier, held at a Store.
_Avoid_: Challenge event, tourney

**Store**:
The venue hosting a League Cup or League Challenge, as named on the event locator.
_Avoid_: Location, shop, venue

### Posting

**Month Post**:
A single Discord message covering every tournament of one tier falling in one
calendar month. Where a month's tournaments exceed what one message can hold, the
Month Post is delivered as several messages that together form one Month Post.
_Avoid_: Message, digest, event list

**Archived Month Post**:
A Month Post for a month that no longer appears in the current tournament data,
because every tournament in it has passed. Archived Month Posts are deliberately
left in the channel as a record of tournaments that have happened, and are never
deleted by the bot.
_Avoid_: Old post, stale post, orphan

**Refresh**:
Replacing the Month Posts for the months present in the current tournament data,
by deleting the bot's existing Month Posts for exactly those months and posting
them again. A Refresh never touches an Archived Month Post.
_Avoid_: Cleanup, purge, delete old messages
