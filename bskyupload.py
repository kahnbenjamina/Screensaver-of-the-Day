import os

from atproto import Client, Request, client_utils, models
from pathlib import Path
from dotenv import load_dotenv
from httpx import Timeout

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

    with open(Path.joinpath(pathdir, "videos", f"{row['key']}.mp4"), 'rb') as f:
        vid_data = f.read()

    aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(height=int(row['vidheight']), width=int(row['vidwidth']))

    # post text
    text_builder = client_utils.TextBuilder()
    text_builder.tag('#ScreensaverOTD', 'ScreenSaverOTD')
    text_builder.text(f" - {date}:\n{row['fullname']}\n\nYear: {row['year']}\nCreator: {row['creator']}\nProduct: {row['product']}\nPublisher: {row['publisher']}\nSystems: {row['os']}\nResolution: {row['vidheight']}x{row['vidwidth']}\n\n")
    text_builder.tag('#Screensaver', 'Screensaver')
    text_builder.text(" ")
    text_builder.tag('#RetroComputing', 'RetroComputing')

    client.send_video(text=text_builder, video=vid_data, video_alt=alttext, video_aspect_ratio=aspect_ratio, langs=['en-US'])