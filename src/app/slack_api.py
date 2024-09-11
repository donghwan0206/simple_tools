import slack_sdk


def send_msg_to_channel(msg, channel, bot_token):
    client = slack_sdk.WebClient(token=bot_token)
    response = client.chat_postMessage(channel=channel, text=msg)
    return response
