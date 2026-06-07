# Screensaver of the Day

<p>This is a script that powers a Bluesky bot which posts a randomly selected pre-recorded screensaver video and some info about it from a database daily at 12:00 UTC.</p>
<p>You can find the link to the bot <a href="https://bsky.app/profile/screensaverotd.bsky.social" target="_blank" rel="noopener noreferrer">here</a>.</p>
<p>It also has functionality to upload any unuploaded screensavers to the <a href="https://www.youtube.com/@ScreensaverMuseum" target="_blank" rel="noopener noreferrer">Screensaver Museum</a> YouTube channel.</p>
<p>For a list of FAQs about this project: please visit the <a href="https://sotdfaq.neocities.org/" target="_blank" rel="noopener noreferrer">FAQs website</a>.</p>

## Requirements

- <code>sotd.py</code> is the main file that drives the whole operation. <code>bskyupload.py</code> is the file that handles uploading to Bluesky.
- Optionally, <code>ytupload.py</code> handles uploading the videos to YouTube. You can comment its functionality out of <code>sotd.py</code> if you would like to ignore this feature.
- The screensaver database file (<code>ScreenSaverOTD.db</code>) in the root directory of the project. You can refer to the included <code>Sample.db</code> to see an example of the database schema the code is looking for.
- An environment file (<code>.env</code>) in the root directory of the project with two variables:
    - <code>ACCTNAME</code>: The name of the Bluesky account.
    - <code>APPID</code>: The app password you generated in the above Bluesky account.
- Python requirements can be found in the file <code>requirements.txt</code>. It can be easily installed using <code>python install -r requirements.txt</code>.
- A directory <code>videos</code> in the root directory of the project which contains .mp4 files titled following the keys in <code>ScreensaverOTD.db</code>. Note: videos uploaded to Bluesky must be **under 300 MB** and **under three minutes** in length.
- For YouTube uploads, you will need a <code>client_secrets.json</code> file which contains your Google OAuth client ID and secret variables. The Google Cloud Console should give an option to directly download this file.
- NOTE: The refresh access tokens for Google OAuth expire after **7 days** and require manual browser-based reauthentication. The code currently accounts for token expiry errors in order to not break. In the future, I will look into ways around this, but from quick research, this just seems to be a built-in limitation. EDIT (2026-06-05): It seems like the OAuth expiry isn't actually a thing? Will do more testing.

## To Do

- Logging
- Direct Message forwarding
- Front end for analysis
- Theme Days/Weeks
- Full Website

## Version History/Changelog

<strong>v1.0</strong> - <em>2025-10-21</em>: First official release. Posts a random screensaver to Bluesky once daily at 12:00 PM UTC. Includes relevant information which is pulled from a locally maintained database file and a locally saved video file. Launched with <em>51</em> screensavers supported and <em>179</em> in the database.

<em>2025-10-28</em>: Discovered some incorrect info in the database. Corrected it.

<em>2025-12-10</em>: Recorded 24 new screensavers and rerecorded 1 existing. Realized that one screensaver was incorrectly named, so that was fixed. Total screensavers recorded up to <em>75</em> now.

<em>2026-02-01</em>: Recorded 16 new screensavers and added 1 new one to the database. Total screensavers recorded up to <em>91</em> now and total in database up to <em>180</em>. Created the FAQ site (<code>sotdfaq.html</code>, <code>sotd.css</code>, and <code>robots.txt</code>) for answering basic questions.

<em>2026-02-03</em>: Made updates to refine the website. Added <code>favicon.ico</code> and <code>toaster.png</code> and put them into the <code>faqsite</code> subfolder along with the three existing website files. Renamed <code>sotdfaq.html</code> to <code>index.html</code>.

<em>2026-03-01</em>: Discovered and fixed an edge case where a failed connection to Bluesky meant the database was updated as if a screensaver was uploaded even if it wasn't. Access to Bluesky is now confirmed before the database is accessed. 1 new screensaver added to the database, <em>181</em> now in total.

<strong>v1.1</strong> - <em>2026-04-18</em>: Large update. Added support for YouTube uploading of screensavers if they haven't already. Changed main script (<code>sotd.py</code>) to mainly focus on selecting from the DB and calling writing functions. Code is now more modular and other APIs can relatively easily be slotted in. Each service can have its own script now (i.e., <code>bskyupload.py</code> and <code>ytupload.py</code>.) Also tweaked some logic to make pulling from the DB more robust and added to the DB a new field for tracking YouTube uploads. Updated both the website and the README to explain these expanded features. Will likely need some bug fixes in the future. Kept old, working file as <code>sotdold.py</code> just in case. Added 1 new screensaver to the database for a total of <em>182</em> and recorded 31 more to bring the count of availables to <em>122</em>.

<strong>v1.1.1</strong> - <em>2026-05-03</em>: Added functionality for the uploaded YouTube video to be added to playlists by their associated product. Creates the playlist if it doesn't yet exist, adds to the existing playlist if it does. Kept the old, working file as <code>ytuploadold.py</code> just in case. Removed <code>sotdold.py</code> as the updated version was proven to work. Updated <code>Sample.db</code> to include the previously added <code>ytid</code> field discussed in the last update. Recorded 7 more screensavers, bringing the total recorded up to <em>129</em>.

<em>2026-05-11</em>: Discovered two bugs. The first was that the YouTube upload functionality returned the ID of the playlist and not the ID of the video. This has been fixed. The other bug was that YouTube titles are limited to 100 characters and many titles were over that limit. To fix this, I added two new fields to the database, <code>shortname</code> and <code>prodshort</code> which shorten either the full title or the full product name of the screensaver to help it fix under the character limit. Updated <code>Sample.db</code> to reflect this. The code checks if either a short title or a short product name exists and uses that in the title, otherwise just uses the full title or full product name. The video description will always contain the full title and full product name. Also removed try/catch from the <code>ytupload</code> function in <code>ytupload.py</code> as it was being duplicated in <code>sotd.py</code>.