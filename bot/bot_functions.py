def format_message(event_dict):
    date = event_dict['when'].split(',')[0]
    time = event_dict['when'].split(" ")[-1]
    store = event_dict['store']
    name = event_dict['name']

    messageText = f"__{name}__\n{date} - {store}\nStart Time: {time}\n"

    return messageText


def get_months(event_dict_list):
    current_months = []
    for event in event_dict_list:
        if event['month'] not in current_months:
            current_months.append(event['month'])

    return current_months


async def delete_old_messages(context, user_id, months):
    async for message in context.channel.history(limit=50):
        for month in months:
            if month in (message.content).split("\n")[0] and user_id == message.author.id:
                await message.delete()