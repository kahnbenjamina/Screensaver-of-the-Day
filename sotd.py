import os
import pandas as pd
import sqlite3
import sys

from atproto import Client, Request, client_utils, models
from datetime import datetime
from dotenv import load_dotenv
from httpx import Timeout
from pathlib import Path

from bluesky import *
from emailrecap import sendEmail
from youtube import *


pathdir = Path(__file__).parent

env_path = Path.joinpath(pathdir, '.env')
load_dotenv(dotenv_path=env_path)

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

# attemps to select new (not uploaded to youtube yet) screensavers first
newQuery = "SELECT * FROM scrnsvrotd WHERE active=1 AND used=0 AND ytid IS NULL ORDER BY RANDOM()" 
query = cur.execute(newQuery)

try:
    output = query.fetchone()
except TypeError as e: # if there are no new active screensavers
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
        cur.execute(f"UPDATE scrnsvrotd SET used = 1, lastused = {date}, timesused = {output['timesused']+1}, ytid = {id} WHERE key = {output['key']}")
    except Exception as e: # if the video can't be uploaded, don't break the database
        print(f"YouTube video upload failed due to: {e}")
        cur.execute(f"UPDATE scrnsvrotd SET used = 1, lastused = {date}, timesused = {output['timesused']+1} WHERE key = {output['key']}")
else: # do not upload if an instance of the video has already been uploaded
    cur.execute(f"UPDATE scrnsvrotd SET used = 1, lastused = {date}, timesused = {output['timesused']+1} WHERE key = {output['key']}")

# only runs analytics related tasks once a week (on Sundays)
if datetime.today().weekday() == 6:
    try:
        notifs = bskynotifs(client)
        dms = bskydms(client)
        notifs.extend([len(dms), len(pd.unique(dms['sender'])), len(dms[dms['newConvo'] == True])])
        notifs = str(notifs).replace('[', '(').replace(']', ')')
        cur.execute(f"INSERT INTO bskystats VALUES {notifs}")
    except Exception as e:
        print(f"Bluesky data pull failed due to {e}")

    try:
        ytstats = ytanalytics(pathdir)['rows']
        cur.executemany("INSERT OR REPLACE INTO ytstats VALUES(?,?,?,?,?,?,?,?,?,?,?,?);", ytstats)
        # the above statement has a bug where it still inputs duplicate rows depsite "REPLACE," so the below statement removes duplicate entries
        # TO DO: figure out how to handle this more elegantly in one statement
        cur.execute("DELETE FROM ytstats WHERE rowid NOT IN (SELECT MIN(rowid) FROM ytstats GROUP BY date)")
    except Exception as e:
        print(f"YouTube data pull failed due to {e}")

    conn.commit() # commits newly pulled data so the new data can be queried

    # attempts to receive last two weeks for both datasets
    ytquery = pd.read_sql_query(f"SELECT * FROM ytstats ORDER BY date DESC LIMIT 14", conn) # picks the most recent two weeks of results
    bskyquery = pd.read_sql_query(f"SELECT * FROM bskystats ORDER BY weekEndingOn DESC LIMIT 2", conn) # picks the most recent two weeks regardless of when the last pull was

    if not ytquery.empty and not bskyquery.empty:
        sendEmail(ytquery, bskyquery, dms)

conn.commit()
conn.close()
