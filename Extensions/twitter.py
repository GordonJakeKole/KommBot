from discord.ext import commands
import Utils.Config as Config
import tweepy
import asyncio

class TwitterCog(commands.Cog):
    def __init__(self, bot, api, user_ids):
        self.bot = bot
        listener = TweetListener(bot, self, api, user_ids)
        self.stream = tweepy.Stream(auth=api.auth, listener=listener)
        twitters = list(user_ids.keys())
        twitters = [str(user_id) for user_id in twitters]
        self.stream.filter(follow=twitters, is_async=True)
        self.ctx = None

    @commands.command(name='twitter_here')
    async def mark_channel(self, ctx):
        """Post twitter updates to this channel"""
        self.ctx = ctx
        await ctx.send('Posting Twitter updates to this channel.')

    async def send_message(self, text):
        if self.ctx:
            await self.ctx.send(text)

class TweetListener(tweepy.StreamListener):
    def __init__(self, bot, cog, api, user_ids):
        self.api = api
        self.cog = cog
        self.bot = bot
        self.user_ids = user_ids

    def on_status(self, tweet):
        try:
            if self.bot.is_closed():
                self.running = False
                return False
        except:
            self.running = False
            return False
            
        if tweet.user.id in self.user_ids:
            screen_name = self.user_ids[tweet.user.id]
            url = f'https://twitter.com/{screen_name}/status/{tweet.id_str}'
            asyncio.run_coroutine_threadsafe(self.cog.send_message(url), self.bot.loop)

    def on_error(self, status_code):
        if status_code == 420:
            return False

def setup(bot):
    data = Config.get_data()
    
    twitter_data = data['twitter']
    consumer_key = twitter_data['consumer_key']
    consumer_key_secret = twitter_data['consumer_key_secret']
    access_token = twitter_data['access_token']
    access_token_secret = twitter_data['access_token_secret']

    auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    acct_names = twitter_data['acct_names']
    users = api.lookup_users(screen_names=acct_names)
    user_ids = {user.id : user.screen_name for user in users}
    
    bot.add_cog(TwitterCog(bot, api, user_ids))
    print('Twitter extension loaded.')
