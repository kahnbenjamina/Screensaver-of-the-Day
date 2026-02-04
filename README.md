# Screensaver of the Day

<p>This is a script that powers a Bluesky bot which posts a randomly selected pre-recorded screensaver video and some info about it from a database daily at 12:00 UTC.</p>
<p>You can find the link to the bot <a href="https://bsky.app/profile/screensaverotd.bsky.social">here</a>.</p>


## Requirements

- The screensaver database file (<code>ScreenSaverOTD.db</code>) in the root directory of the project. You can refer to the included <code>Sample.db</code> to see an example of the database schema the code is looking for.
- An environment file (<code>.env</code>) in the root directory of the project with two variables:
    - <code>ACCTNAME</code>: The name of the Bluesky account.
    - <code>APPID</code>: The app password you generated in the above Bluesky account.
- Python requirements can be found in the file <code>requirements.txt</code>. It can be easily installed using <code>python install -r requirements.txt</code>.
- A directory <code>videos</code> in the root directory of the project which contains .mp4 files titled following the keys in <code>ScreensaverOTD.db</code>. Note, videos uploaded to Bluesky must be **under 100 MB** and **under three minutes** in length.

## To Do

- Logging
- Direct Message forwarding
- Front end for analysis
- Themes

## Version History/Changelog

<strong>v1.0</strong> - <em>2025-10-21</em>: First official release. Posts a random screensaver to Bluesky once daily at 12:00 PM UTC. Includes relevant information which is pulled from a locally maintained database file and a locally saved video file. Launched with <em>51</em> screensavers supported and <em>179</em> in the database.

<em>2025-10-28</em>: Discovered some incorrect info in the database. Corrected it.

<em>2025-12-10</em>: Recorded 24 new screensavers and rerecorded 1 existing. Realized that one screensaver was incorrectly named, so that was fixed. Total screensavers recorded up to <em>75</em> now.

<em>2026-02-01</em>: Recorded 16 new screensavers and added 1 new one to the database. Total screensavers recorded up to <em>91</em> now and total in database up to <em>180</em>. Created the FAQ site (<code>sotdfaq.html</code>, <code>sotd.css</code>, and <code>robots.txt</code>) for answering basic questions.

<em>2026-02-03</em>: Made updates to refine the website. Added <code>favicon.ico</code> and <code>toaster.png</code> and put them into the <code>faqsite</code> subfolder along with the three existing website files. Renamed <code>sotdfaq.html</code> to <code>index.html</code>.
