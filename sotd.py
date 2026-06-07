import os
import sqlite3
import sys
import pandas as pd

from datetime import datetime
from pathlib import Path

from atproto import Client, Request, client_utils, models
from dotenv import load_dotenv
from httpx import Timeout

from bskyupload import *
from ytupload import *

pathdir = Path(__file__).parent

date = datetime.today().strftime('%Y-%m-%d')

# in the event Bluesky cannot be connected to, break early so the database is not affected
try:
    client = bskyconn(pathdir)
except:
    sys.exit("Connection to Bluesky failed.")

# place .db file in root directory of project
conn = sqlite3.connect(Path.joinpath(pathdir, 'ScreensaverOTD.db'))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# only selects screensavers with videos (active) and that haven't been used since the last reset (used)
fullQuery = "SELECT * FROM scrnsvrotd WHERE active=1 AND used=0 ORDER BY RANDOM()"

query = cur.execute(fullQuery)

try:
    output = query.fetchone()
except TypeError as e: # if there are no unused active screensavers, resets all active to unused
    cur.execute("UPDATE scrnsvrotd SET used = 0 WHERE used = 1")
    query = cur.execute(fullQuery)
    output = query.fetchone()

bskyupload(output, date, pathdir, client)

# if the video hasn't been uploaded to YouTube yet
if output['ytid'] is None:
    try: # saves the id of the video to the database
        id = ytupload(output, pathdir)
        cur.execute("UPDATE scrnsvrotd SET used = 1, lastused = ?, timesused = ?, ytid = ? WHERE key = ?", (date, output['timesused']+1, id, output['key']))
    except Exception as e: # if the video can't be uploaded, don't break the database
        print(e)
        cur.execute("UPDATE scrnsvrotd SET used = 1, lastused = ?, timesused = ? WHERE key = ?", (date, output['timesused']+1, output['key']))
else: # do not upload if an instance of the video has already been uploaded
    cur.execute("UPDATE scrnsvrotd SET used = 1, lastused = ?, timesused = ? WHERE key = ?", (date, output['timesused']+1, output['key']))

if datetime.today().weekday() == 6:
    notifs = bskynotifs(client)
    dms = bskydms(client)
    notifs.extend([len(dms), len(pd.unique(dms['sender'])), len(dms[dms['newConvo'] == True])])
    notifs = str(notifs).replace('[', '(').replace(']', ')')
    cur.execute(f"INSERT INTO bskystats VALUES {notifs}")

    ytstats = ytanalytics(pathdir)['rows']
    cur.executemany("INSERT INTO ytstats VALUES(?,?,?,?,?,?,?,?,?,?,?,?);", response)

conn.commit()
conn.close()
