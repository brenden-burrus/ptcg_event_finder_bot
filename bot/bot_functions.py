def format_message(event_dict):
    date = event_dict['when'].split(',')[0]
    time = event_dict['when'].split(" ")[-1]
    store = event_dict['store']
    name = event_dict['name']

    messageText = f"**{name}**\n{date} - {store}\nStart Time: {time}\n"

    return messageText


def get_months(event_dict_list):
    current_months = []
    for event in event_dict_list:
        if event['month'] not in current_months:
            current_months.append(event['month'])

    return current_months