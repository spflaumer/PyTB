#    PyTB - a very basic (to be expanded) Discord Bot to scrape Twitter and notify a Server
#    Copyright (C) 2023  Simon "spflaumer" Pflaumer
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


from snscrape.modules import twitter
import pandas as pd
import datetime as dt

import discord
from discord.ext import tasks

username = "@KIRUNO_RUKI" # twitter username to be tracked
channel_id = 1091073028944842904 # the id of the channel where the updates should be sent to
interval = 0.5 # interval (60 second == 1)
bot_token = '' # the bot token as a string

def get_tweets(username: str, since: dt.datetime, n: int):
    tweetlist = [] # initialize empty list
    since_str = since.strftime("%Y-%m-%d") # since when to query formatted as a twitter friendly string

    i = 0
    for i, t in enumerate(twitter.TwitterSearchScraper(f"from:{username} since:{since_str}").get_items(), start = 1):
        if i > n: break # stop looking for tweets if number of tweets exceeds desired number of tweets `n`
        tweetlist.append([t.date, t]) # append the tweets date and link to the list of collected tweets

    tweets_dataframe = pd.DataFrame(tweetlist, columns = ['Date', 'TweetLink']) # create a pandas DataFrame

    return tweets_dataframe

class PyTB(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tweets = pd.DataFrame([], columns = ['Date', 'TweetLink'])
        self.ntweets = 2
        self.wait = 5
    async def setup_hook(self) -> None:
        self.tweet_scraper.start()
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')


    async def handle_tweets(self, tweets: pd.DataFrame):
        if (not tweets.empty and not self.tweets.empty): # exit if no tweets were found
            if (tweets.loc[0, 'Date'] <= self.tweets.loc[0, 'Date']): #exiut if no new tweets were found
                return

            channel = self.get_channel(channel_id)

            await channel.send(f"{tweets.loc[0, 'TweetLink']}") # send the link to the Tweet into the channel
        else: 
            return

    @tasks.loop(seconds=(interval*60))
    async def tweet_scraper(self):
        since = (dt.datetime.now() - dt.timedelta(days = 1))
        tweets = get_tweets(username, since, self.ntweets) # get `self.ntweets` amount of tweets, since `since` and from `username`

        await self.handle_tweets(tweets) # handle the result

        self.tweets = tweets # save current fetched tweets for comparison in `self.handle_tweets()`


    @tweet_scraper.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

client = PyTB(intents=intents)
client.run(bot_token)
