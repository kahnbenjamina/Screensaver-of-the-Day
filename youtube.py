import google_auth_oauthlib.flow
import google.oauth2.credentials
import httplib2
import os
import random
import sys
import time

from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from pathlib import Path


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google API Console at
# https://console.cloud.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows an application to access the authenticated user's YouTube channel.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.cloud.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

# checks the generated json file which includes the name of this file (for upload API)
def get_authenticated_service_up(pathdir):
  flow = flow_from_clientsecrets(pathdir.joinpath(CLIENT_SECRETS_FILE),
    scope=YOUTUBE_UPLOAD_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage(pathdir.joinpath(f"{Path(__file__).name}-oauth2.json"))
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, pathdir.joinpath(f"{Path(__file__).name}-oauth2.json"))

  http=credentials.authorize(httplib2.Http())

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http)

# creates a new playlist
def newplaylist(youtube, product):
  body=dict(
    snippet=dict(
      title=product
    ),
    status=dict(
      privacyStatus="public",
    )
  )

  # Call the API's playlists.insert method to create the new playlist.
  newpl = youtube.playlists().insert(
    part=",".join(body.keys()),
    body=body
  )

  response = newpl.execute()

  return response['id']

# code to handle returning the id of the required playlist (existing or newly created)
def playlist(youtube, product):
  # Call the API's playlists.list method to get a list of the IDs and info about each playlist.
  getlist = youtube.playlists().list(
    part="id, snippet",
    maxResults=100,
    mine=True
  )
  response = getlist.execute()

  plids = [element['id'] for element in response['items']] # playlist IDs
  pltitles = [element['snippet']['title'] for element in response['items']] # playlist names

  # if the required playlist already exists
  if product in pltitles:
    id = plids[pltitles.index(product)]
    print(f"{product} playlist found!")
  else: # if the required playlist doesn't exist, make it
    id = newplaylist(youtube, product)
    print(f"{product} playlist created!")

  return id

# the metadata of the video and the command to upload it
def initialize_upload(youtube, row, plid):
  # YouTube's title caps out at 100 characters
  name = row['shortname'] if row['shortname'] is not None else row['fullname']
  prod = row['prodshort'] if row['prodshort'] is not None else row['product']
  
  # Generate the video's metadata
  body=dict(
    snippet=dict(
      title=f'"{name}" screensaver from {prod} ({row['year']})',
      description=(
        f"Full Name: {row['fullname']}\n\n"
        f"Year: {row['year']}\n"
        f"Creator: {row['creator']}\n"
        f"Product: {row['product']}\n"
        f"Publisher: {row['publisher']}\n"
        f"Native OS: {row['os']}\n"
        f"Original Resolution: {row['vidheight']}x{row['vidwidth']}\n\n"
        f"More from this product: https://www.youtube.com/playlist?list={plid}\n\n"
        f"For daily screensavers, check out the Screensaver of the Day Bluesky account: bsky.app/profile/screensaverotd.bsky.social\n"
        f"For more information on the project, check out the FAQs: sotdfaq.neocities.org"
      ),
      tags=['screensaver', 'screensavers' 'retrocomputing', 'screensavermuseum'],
      categoryId="28" # Science and Technology
    ),
    status=dict(
      privacyStatus="public",
      embeddable=True,
      selfDeclaredMadeForKids=False
    )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    media_body=MediaFileUpload(Path.joinpath(Path(__file__).parent, "videos", f"{row['key']}.mp4"), chunksize=-1, resumable=True)
  )

  return resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print ("Uploading file...")
      status, response = insert_request.next_chunk()
      if response is not None:
        if 'id' in response:
          print ("Video id '%s' was successfully uploaded." % response['id'])
        else:
          exit("The upload failed with an unexpected response: %s" % response)
    except HttpError as e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS as e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print (error)
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print ("Sleeping %f seconds and then retrying..." % sleep_seconds)
      time.sleep(sleep_seconds)
  
  return response['id']

# adds the newly uploaded video to the proper playlist
def vid2pl(youtube, plid, vidid):
  body=dict(
    snippet=dict(
      playlistId=plid,
      resourceId=dict(
        kind="youtube#video",
        videoId=vidid
      )
    )
  )

  # Call the API's playlistItems.insert method to add the video to the specific playlist.
  plinsert = youtube.playlistItems().insert(
    part=",".join(body.keys()),
    body=body
  )

  response = plinsert.execute()

  return response['id']

# function to be run by main
def ytupload(row, pathdir):
  # authenticates youtube access
  youtube_u = get_authenticated_service_up(pathdir)

  # gets id of playlist (and may create new playlist)
  plid = playlist(youtube_u, row['product'])

  # uploads the video and adds it to the proper playlist (try, except handled in main)
  vidid = initialize_upload(youtube_u, row, plid)
  id = vid2pl(youtube_u, plid, vidid)

  return vidid # id of the uploaded video


# FOR ANALYTICS  

YOUTUBE_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
ANALYTICS_API_SERVICE_NAME = "youtubeAnalytics"
ANALYTICS_API_VERSION = "v2"

# checks the generated json file which includes the name of this file (for analytics API)
def get_authenticated_service_data(pathdir):
  flow = flow_from_clientsecrets(pathdir.joinpath(CLIENT_SECRETS_FILE),
    scope=YOUTUBE_ANALYTICS_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage(pathdir.joinpath(f"{Path(__file__).name}-oauth2.json"))
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, pathdir.joinpath(f"{Path(__file__).name}-oauth2.json"))

  http=credentials.authorize(httplib2.Http())

  return build(ANALYTICS_API_SERVICE_NAME, ANALYTICS_API_VERSION, http)

def execute_api_request(client_library_function, **kwargs):
  response = client_library_function(
    **kwargs
  ).execute()

  return response

# analytics function to be called by main
def ytanalytics(pathdir):
  youtube_d = get_authenticated_service_data

  # YouTube data is not available for a day until a day or two at least after that day
  # YouTube data does not seem to "finalize" until after about a week, so it pulls further back than a week and overwrites old data
  response = execute_api_request(
      youtube_d.reports().query,
      ids='channel==MINE',
      startDate=datetime.now().date() - timedelta(days=10),
      endDate=datetime.now().date(),
      metrics='views,engagedViews,comments,likes,dislikes,shares,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost',
      dimensions='day',
      sort='day'
  )

  return response