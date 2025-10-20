# Screensaver of the Day

<p>This is a script that powers a Bluesky bot which posts a randomly selected pre-recorded screensaver video and some info about it from a database daily at 12:00 UTC.</p>
<p>You can find the link to the bot [here](https://bsky.app/profile/screensaverotd.bsky.social).</p>


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