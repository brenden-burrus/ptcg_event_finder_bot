def format_message(event_dict):
    date = event_dict['date']
    time = event_dict['time']
    store = event_dict['store']
    name = event_dict['name']
    tourney_page = event_dict['tourney_page']

    messageText = f"__{name}__\n{date} - {store}\nStart Time: {time}\n[Tournament Link]({tourney_page})\n"

    return messageText


def get_months(event_dict_list):
    current_months = []
    for event in event_dict_list:
        if event['date'].split(' ')[0] not in current_months:
            current_months.append(event['date'].split(' ')[0])

    return current_months


async def delete_old_messages(context, user_id, months):
    async for message in context.channel.history(limit=50):
        for month in months:
            if month in (message.content).split("\n")[0] and user_id == message.author.id:
                await message.delete()