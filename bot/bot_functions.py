# Discord rejects a message whose content runs past this, with a 400 and error
# code 50035. It is a parameter of build_month_posts rather than a constant read
# inside it so tests can provoke a split without building a realistic month.
DISCORD_MESSAGE_LIMIT = 2000


def build_month_posts(title, events, limit=DISCORD_MESSAGE_LIMIT):
    """Render one month's events as the messages making up its Month Post.

    Takes the title rather than a finished header, because a Month Post split
    across messages numbers each one *inside* the header's emphasis, and only a
    Month Post that fits in one message keeps the plain header.
    """
    # How wide the header is depends on how many messages there turn out to be,
    # which packing needs to know before it starts. A Month Post can never need
    # more messages than it has events, so a header numbered against the event
    # count is a safe upper bound -- reserve that and pack once.
    reserve = len(_month_post_prefix(title, len(events), len(events)))
    budget = limit - reserve
    if budget < 1:
        raise ValueError(
            f"a limit of {limit} leaves no room for events under a "
            f"{reserve}-character header for {title!r}"
        )

    groups = []
    current = []
    used = 0
    for event in (_truncate_to_fit(event, budget) for event in events):
        # Packing is greedy, and only ever breaks between events -- half an
        # address split across two messages is worse than an extra message.
        if current and reserve + used + len(event) > limit:
            groups.append(current)
            current, used = [], 0
        current.append(event)
        used += len(event)
    if current:
        groups.append(current)

    total = len(groups)
    return [
        _month_post_prefix(title, n, total) + "".join(group)
        for n, group in enumerate(groups, start=1)
    ]


def _truncate_to_fit(event, budget):
    """Cut a single event down to what one message can hold.

    No event is anywhere near this today -- the longest observed is 207
    characters against a 2000 limit -- but an event that cannot fit alone has
    to go somewhere. Truncating keeps the tournament visible; dropping it would
    hide a tournament, and passing it through would raise the same 400 this
    whole function exists to prevent.
    """
    if len(event) <= budget:
        return event
    if budget <= 4:
        return event[:budget]
    return event[: budget - 4].rstrip() + "...\n"


def _month_post_prefix(title, position, total):
    """Everything before the first event: the header and its blank line.

    The reserve packing works against is the length of this, so the header and
    the separator have to be built in one place -- widening the separator here
    must narrow the budget with it.
    """
    if total == 1:
        return f"# *{title}*\n\n"
    return f"# *{title} ({position} of {total})*\n\n"


def format_message(event_dict):
    print(event_dict)
    date = event_dict['date']
    # time = event_dict['time']
    store = event_dict['store']
    name = event_dict['name']
    address = event_dict['tourney_address']
    tourney_page = event_dict['tourney_page']

    messageText_old = f"__{name}__\n{store}\nDate: {date}\nAddress: {address}\n[Tournament Link]({tourney_page})\n"
    messageText = f"__{name}__\n{store}\nDate: {date}\nAddress: {address}\n"
    print(f"Length of original message: {len(messageText_old)}")
    print(f"Length of new message: {len(messageText)}")

    return messageText


def get_months(event_dict_list):
    current_months = []
    for event in event_dict_list:
        if event['date'].split(' ')[1] not in current_months:
            current_months.append(event['date'].split(' ')[1])
    return current_months

async def delete_old_messages(context, user_id, months):
    async for message in context.channel.history(limit=50):
        for month in months:
            if month in (message.content).split("\n")[0] and user_id == message.author.id:
                await message.delete()
