# Refresh matches Month Posts on the first line only

A Refresh finds the bot's existing Month Posts by checking whether a month name
appears in the **first line** of a message — the header line — and nowhere else.
This looks needlessly narrow, and the obvious "improvement" is to match the month
anywhere in the message body. Do not make that change: it silently destroys
Archived Month Posts, which users value as a record of tournaments that have
happened, and deletion is not recoverable.

## Considered Options

- **Match the month anywhere in the message content.** Rejected. Play! Pokémon
  organisers routinely put a month name in the event *title* — of the fifteen
  League Challenges scraped on 2026-09-07, eight had one, including "WGG September
  Challenge" and "September 2026 League Challenge". A store that names an event
  "September Challenge" but schedules it in October puts the word "September"
  inside an **October** Month Post, which a body-wide match then deletes while
  September is still in the current data.
- **Delete every message the bot authored in the channel.** Rejected. The channels
  currently hold nothing but this bot's output, so it would work today, but it
  deletes every Archived Month Post along with it.

## Consequences

Every message making up a split Month Post must carry a header line containing its
month, including continuation messages. That is why continuation headers exist and
why a Month Post is not split into headerless messages — the header is what makes
the message findable at the next Refresh.
