import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from atproto import Client, Request, client_utils, models
from dotenv import load_dotenv
from httpx import Timeout

pathdir = Path(__file__).parent

date = datetime.today().strftime('%Y-%m-%d')

# in the event Bluesky cannot be connected to, break early so the database is not affected
try:
    env_path = Path.joinpath(pathdir, '.env')
    load_dotenv(dotenv_path=env_path)

    # bluesky account name and app ID from .env file in root directory of project
    user = os.getenv("ACCTNAME")
    pw = os.getenv("APPID")

    request = Request(timeout=Timeout(timeout=None)) # no timeout on the client, it's normally quite strict

    client = Client(request=request)
    client.login(user, pw)
except:
    sys.exit("Connection to Bluesky failed.")

# place .db file in root directory of project
conn = sqlite3.connect(Path.joinpath(pathdir, 'ScreensaverOTD.db'))
cur = conn.cursor()

# only selects screensavers with videos and that haven't been used since the last reset
fullQuery = "SELECT key, fullname, year, creator, product, publisher, os, vidheight, vidwidth, timesused FROM scrnsvrotd WHERE active=1 AND used=0 ORDER BY RANDOM()"

query = cur.execute(fullQuery)

try:
    key, fullname, year, creator, product, publisher, system, horiz, vert, times = query.fetchone()
except TypeError as e: # if there are no unused active screensavers, resets all active to unused
    cur.execute("UPDATE scrnsvrotd SET used = 0 WHERE used = 1")
    query = cur.execute(fullQuery)
    key, fullname, year, creator, product, publisher, system, horiz, vert, times = query.fetchone()

cur.execute("UPDATE scrnsvrotd SET used = 1, lastused = ?, timesused = ? WHERE key = ?", (date, times+1, key))

conn.commit()
conn.close()

alttext = f"A video of the screensaver {fullname} created by {creator} in {year} for {product} on {system}."

with open(Path.joinpath(pathdir, "videos", f"{key}.mp4"), 'rb') as f:
    vid_data = f.read()

aspect_ratio = models.AppBskyEmbedDefs.AspectRatio(height=int(horiz), width=int(vert))

# post text
text_builder = client_utils.TextBuilder()
text_builder.tag('#ScreensaverOTD', 'ScreenSaverOTD')
text_builder.text(f" - {date}:\n{fullname}\n\nYear: {year}\nCreator: {creator}\nProduct: {product}\nPublisher: {publisher}\nSystems: {system}\nResolution: {horiz}x{vert}\n\n")
text_builder.tag('#Screensaver', 'Screensaver')
text_builder.text(" ")
text_builder.tag('#RetroComputing', 'RetroComputing')

client.send_video(text=text_builder, video=vid_data, video_alt=alttext, video_aspect_ratio=aspect_ratio, langs=['en-US'])
