import os
import pandas as pd

from atproto import Client, Request, client_utils, models, IdResolver
from pathlib import Path
from dotenv import load_dotenv
from httpx import Timeout
from datetime import datetime, timedelta

def bskyconn(pathdir):
    env_path = Path.joinpath(pathdir, '.env')
    load_dotenv(dotenv_path=env_path)

    # bluesky account name and app ID from .env file in root directory of project

    user = os.getenv("ACCTNAME")
    pw = os.getenv("APPID")

    request = Request(timeout=Timeout(timeout=None)) # no timeout on the client, it's normally quite strict

    client = Client(request=request)
    client.login(user, pw)

    return client

def bskyupload(row, date, pathdir, client):
    alttext = f"A video of the screensaver {row['fullname']} created by {row['creator']} in {row['year']} for {row['product']} on {row['os']}."
    posttext = (
        f" - {date}:\n"
        f"{row['fullname']}\n\n"
        f"Year: {row['year']}\n"
        f"Creator: {row['creator']}\n"
        f"Product: {row['product']}\n"
        f"Publisher: {row['publisher']}\n"
        f"Systems: {row['os']}\n"
        f"Resolution: {row['vidheight']}x{row['vidwidth']}\n\n"
    )

    with open(Path.joinpath(pathdir, "videos", f"{row['key']}.mp4"), 'rb') as f:
        vid_data = f.read()

    aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(height=int(row['vidheight']), width=int(row['vidwidth']))

    # post text
    text_builder = client_utils.TextBuilder()
    text_builder.tag('#ScreensaverOTD', 'ScreenSaverOTD')
    text_builder.text(posttext)
    text_builder.tag('#Screensaver', 'Screensaver')
    text_builder.text(" ")
    text_builder.tag('#RetroComputing', 'RetroComputing')

    client.send_video(text=text_builder, video=vid_data, video_alt=alttext, video_aspect_ratio=aspect_ratio, langs=['en-US'])

def bskydms(client):
    # create client proxied to Bluesky Chat service
    dm_client = client.with_bsky_chat_proxy()
    # create shortcut to convo methods
    dm = dm_client.chat.bsky.convo

    id_resolver = IdResolver()

    msgList = pd.DataFrame(columns=['sender', 'message', 'timesent', 'newConvo'])

    convo_list = dm.list_convos({"read_state": "unread"}) # use limit and cursor to paginate
    for convo in convo_list.convos:
        replyCheck = True
        if convo.status != 'accepted':
            dm.accept_convo({"convo_id": convo.id})
        discussion = dm.get_messages({"convo_id": convo.id})
        format = '%Y-%m-%dT%H:%M:%S.%fZ'
        for message in discussion.messages:
            sender = id_resolver.did.resolve(message.sender.did).also_known_as[0][5:]
            if sender == os.getenv("ACCTNAME"):
                replyCheck = False
            if (datetime.utcnow() - datetime.strptime(message.sent_at, format)) < timedelta(weeks=1) and sender != os.getenv("ACCTNAME"):
                msgList.loc[len(msgList)] = [sender, message.text, message.sent_at, False]
        if replyCheck:
            message = dm.send_message(
                models.ChatBskyConvoSendMessage.Data(
                    convo_id=convo.id,
                    message=models.ChatBskyConvoDefs.MessageInput(
                        text=(
                            "Thank you for your message! It has been received, and a response should be coming here in a day or so.\n\n"
                            "Please note this account is not actively monitored. Any future messages will be responded to within about a week. You will not receive another confirmation message.\n\n" 
                            f"You can email {os.getenv('EMAIL')} for faster responses.\n\n"
                            "[THIS IS AN AUTOMATED MESSAGE]"
                        )
                    ),
                )
            )
            newuser = msgList[msgList['sender'] == sender].index[0]
            msgList.loc[msgList.index.get_loc(newuser), 'newConvo'] = True

    return msgList

def bskynotifs(client):
    response = client.app.bsky.notification.list_notifications()

    knownValues = [
            "like",
            "repost",
            "follow",
            "mention",
            "reply",
            "quote",
            "starterpack-joined",
            "verified",
            "unverified",
            "like-via-repost",
            "repost-via-repost"
          ]
          
    notifs = []
    counts = []

    for notification in response.notifications:
        if not notification.is_read:
            notifs.append(notification.reason)

    for val in knownValues:
        counts.append(notifs.count(val))

    counts.insert(0, datetime.today().strftime('%Y-%m-%d'))

    client.app.bsky.notification.update_seen({'seen_at': client.get_current_time_iso()})

    return counts