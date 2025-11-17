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
