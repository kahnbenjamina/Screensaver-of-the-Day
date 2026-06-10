import os
import smtplib

from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# returns symbols assuming current value should be higher than previous value
def getCharPos(curVal, prevVal):
    symbol = f''
    if curVal > prevVal:
        symbol = f'<SPAN style="color:green">&#8593;</SPAN> {round(curVal-prevVal, 2)}'
    elif curVal < prevVal:
        symbol = f'<SPAN style="color:red">&#8595;</SPAN> {abs(round(curVal-prevVal, 2))}'
    else:
        symbol = f'<SPAN style="color:gray">&#8596;</SPAN>'

    return symbol

# returns symbols assuming current value should be lower than previous value
def getCharNeg(curVal, prevVal):
    symbol = f''
    if curVal > prevVal:
        symbol = f'<SPAN style="color:red">&#8593;</SPAN> {round(curVal-prevVal, 2)}' 
    elif curVal < prevVal:
        symbol = f'<SPAN style="color:green">&#8595;</SPAN> {abs(round(curVal-prevVal, 2))}'
    else:
        symbol = f'<SPAN style="color:gray">&#8596;</SPAN>'
    
    return symbol

# builds the email text in HTML and sends it off (TO DO: make this less of a mess)
def sendEmail(ytquery, bskyquery, dms):
    email = os.getenv('EMAIL')

    emailplus = email[:email.find('@')] + '+recap' + email[email.find('@'):] # email alias

    message = MIMEMultipart()
    message['From'] = email
    message['To'] = emailplus
    message['Subject'] = f'Screensaver of the Day Weekly Recap for the Week ending on {datetime.now().date()}'

    curYT = ytquery[ytquery['date'] > str(datetime.now().date()-timedelta(days=8))]
    prevYT = ytquery[ytquery['date'] <= str(datetime.now().date()-timedelta(days=8))]

    # YouTube stats section (could try to make this a function, but the different roundings, mean vs sum, pos vs neg make it difficult)
    ytString = (
        f'<P>&emsp;<B>Daily Views</B>: {round(curYT['views'].mean())} ({getCharPos(round(curYT['views'].mean()), round(prevYT['views'].mean()))})</P>\n'
        f'<P>&emsp;<B>Daily Engaged Views</B>: {round(curYT['engagedViews'].mean())} ({getCharPos(round(curYT['engagedViews'].mean()), round(prevYT['engagedViews'].mean()))})</P>\n'
        f'<P>&emsp;<B>Daily Comments</B>: {round(curYT['comments'].mean())} ({getCharPos(round(curYT['comments'].mean()), round(prevYT['comments'].mean()))})</P>\n'
        f'<P>&emsp;<B>Daily Likes</B>: {round(curYT['likes'].mean())} ({getCharPos(round(curYT['likes'].mean()), round(prevYT['likes'].mean()))})</P>\n'
        f'<P>&emsp;<B>Daily Dislikes</B>: {round(curYT['dislikes'].mean())} ({getCharNeg(round(curYT['dislikes'].mean()), round(prevYT['dislikes'].mean()))})</P>\n'
        f'<P>&emsp;<B>Daily Shares</B>: {round(curYT['shares'].mean())} ({getCharPos(round(curYT['shares'].mean()), round(prevYT['shares'].mean()))})</P>\n'
        f'<P>&emsp;<B>Daily Minutes Watched</B>: {round(curYT['estMinsWatched'].mean(), 2)} ({getCharPos(round(curYT['estMinsWatched'].mean(), 2), round(prevYT['estMinsWatched'].mean(), 2))})</P>\n'
        f'<P>&emsp;<B>Average View Duration (secs)</B>: {round(curYT['avgViewDuration'].mean())} ({getCharPos(round(curYT['avgViewDuration'].mean()), round(prevYT['avgViewDuration'].mean()))})</P>\n'
        f'<P>&emsp;<B>Average View Percent</B>: {round(curYT['avgViewPercent'].mean(), 2)}% ({getCharPos(round(curYT['avgViewPercent'].mean(), 2), round(prevYT['avgViewPercent'].mean(), 2))}%)</P>\n'
        f'<P>&emsp;<B>Subscribers Gained</B>: {curYT['subscribersGained'].sum()} ({getCharPos(curYT['subscribersGained'].sum(), prevYT['subscribersGained'].sum())})</P>\n'
        f'<P>&emsp;<B>Subscribers Lost</B>: {curYT['subscribersLost'].sum()} ({getCharNeg(curYT['subscribersLost'].sum(), prevYT['subscribersLost'].sum())})</P>\n'
    )

    curbsky = bskyquery.iloc[0]
    prevbsky = bskyquery.iloc[1]

    # Bluesky stats section (could make this a function, but stat names do not align with )
    bskyString = (
        f'<P>&emsp;<B>Likes</B>: {curbsky['likes']} ({getCharPos(curbsky['likes'], prevbsky['likes'])})</P>\n'
        f'<P>&emsp;<B>Reposts</B>: {curbsky['reposts']} ({getCharPos(curbsky['reposts'], prevbsky['reposts'])})</P>\n'
        f'<P>&emsp;<B>Follows</B>: {curbsky['follows']} ({getCharPos(curbsky['follows'], prevbsky['follows'])})</P>\n'
        f'<P>&emsp;<B>Mentions</B>: {curbsky['mentions']} ({getCharPos(curbsky['mentions'], prevbsky['mentions'])})</P>\n'
        f'<P>&emsp;<B>Replies</B>: {curbsky['replies']} ({getCharPos(curbsky['replies'], prevbsky['replies'])})</P>\n'
        f'<P>&emsp;<B>Quotes</B>: {curbsky['quotes']} ({getCharPos(curbsky['quotes'], prevbsky['quotes'])})</P>\n'
        f'<P>&emsp;<B>Starter Packs</B>: {curbsky['starterpacks']} ({getCharPos(curbsky['starterpacks'], prevbsky['starterpacks'])})</P>\n'
        f'<P>&emsp;<B>Likes via Reposts</B>: {curbsky['likes-via-repost']} ({getCharPos(curbsky['likes-via-repost'], prevbsky['likes-via-repost'])})</P>\n'
        f'<P>&emsp;<B>Reposts via Reposts</B>: {curbsky['reposts-via-repost']} ({getCharPos(curbsky['reposts-via-repost'], prevbsky['reposts-via-repost'])})</P>\n'
        f'<P>&emsp;<B>Total DMs</B>: {curbsky['total-messages']} ({getCharPos(curbsky['total-messages'], prevbsky['total-messages'])})</P>\n'
        f'<P>&emsp;<B>Users DMing</B>: {curbsky['users-messaging']} ({getCharPos(curbsky['users-messaging'], prevbsky['users-messaging'])})</P>\n'
        f'<P>&emsp;<B>New Users DMing</B>: {curbsky['newusers-messaging']} ({getCharPos(curbsky['newusers-messaging'], prevbsky['newusers-messaging'])})</P>\n'
    )

    dmString = f''

    if dms.empty:
        dmString = f"<H3>&emsp; No DMs this week!</H3>"
    else:
        for DMer in dms['sender'].unique():
            subDM = dms[dms['sender'] == DMer].sort_values(by = ['timesent'], ascending = True)
            if "True" in subDM['newConvo'].values:
                dmString = dmString + f"<H3>&emsp; {DMer} <I>new convo</I></H3>\n"
            else:
                dmString = dmString + f"<H3>&emsp; {DMer}</H3>\n"
            for index, row in subDM.iterrows():
                dmString = dmString + f'<P>&emsp; &emsp; {row['message']} <SPAN style="font-size:10px"><I>({row['timesent']})</I></SPAN></P>\n'

    html = f"""\
    <html>
        <head>
            <style>
            </style>
        </head
        <body>
            <H1 style="text-align: center"><B>Here's your weekly recap for the week of {datetime.now().date()}!</B></H1>
            <H2>YouTube Stats (change from previous week)</H2>
            {ytString}
            <H2>Bluesky Weekly Stats (change from previous week)</H2>
            {bskyString}
            <H2>Bluesky Direct Messages</H2>
            {dmString}
        </body>
    </html>
    """

    message.attach(MIMEText(html, 'html'))

    smtp_server = 'smtp.gmail.com'
    port = 587
    password = os.getenv('EMAILPASS')

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(email, password)

    server.send_message(message)
    server.quit()