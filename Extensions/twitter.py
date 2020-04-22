from discord.ext import commands
import Utils.Config as Config
#imports for twitter
import tweepy, asyncio
#imports for azure
import concurrent, requests, uuid, json

class TwitterCog(commands.Cog):
    def __init__(self, bot, cfg):
        self.bot = bot
        self._twitter_setup(bot, cfg)
        self._azure_setup(cfg)
        self.channel = None

    def _twitter_setup(self, bot, cfg):
        twitter_data = cfg['twitter']
        consumer_key = twitter_data['consumer_key']
        consumer_key_secret = twitter_data['consumer_key_secret']
        access_token = twitter_data['access_token']
        access_token_secret = twitter_data['access_token_secret']

        auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        acct_names = twitter_data['acct_names']
        users = api.lookup_users(screen_names=acct_names)
        self.user_ids = {user.id : user.screen_name for user in users}
        
        listener = TweetListener(api, bot, self, self.user_ids)
        self.stream = tweepy.Stream(auth=api.auth, listener=listener, daemon=True)
        self.twitters = list(self.user_ids.keys())
        self.twitters = [str(user_id) for user_id in self.twitters]
        self.stream.filter(follow=self.twitters, is_async=True, stall_warnings=True)

    def _azure_setup(self, cfg):
        azure_data = cfg['azure']
        translate_key = azure_data['translate_key']
        translate_endpoint = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0'
        params = f'&from={azure_data["from_lang"]}&to={azure_data["to_lang"]}'
        self.azure_url = translate_endpoint + params
        self.headers = {
            'Ocp-Apim-Subscription-Key': translate_key,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        self.dynamic_dict = azure_data['dynamic_dict']

    def restart_stream(self):
        self.stream._thread.join()
        self.stream.filter(follow=self.twitters, is_async=True, stall_warnings=True)

    @commands.command(name='check')
    async def check_ctx(self, ctx):
        await ctx.send(f'Stream Running: {self.stream.running}\n'
                       f'Channel Set: {self.channel is not None}')

    @commands.command(name='twitter_here')
    async def change_ctx(self, ctx):
        self.channel = ctx.channel
        await self.channel.send('Sending messages here.')

    async def send_tweet(self, tweet):
        if hasattr(tweet, "retweeted_status"):
            try:
                tweet_text = tweet.retweeted_status.extended_tweet['full_text']
            except AttributeError:
                tweet_text = tweet.retweeted_status.text
        else:
            try:
                tweet_text = tweet.extended_tweet['full_text']
            except AttributeError:
                tweet_text = tweet.text
        tweet_text = tweet_text.replace('#', '# ')
        for original, translation in self.dynamic_dict.items():
            tweet_text = tweet_text.replace(original, f'<mstrans:dictionary translation="{translation}">{original}</mstrans:dictionary>')

        body = [{
            'text' : tweet_text
        }]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            loop = asyncio.get_event_loop()
            post = lambda: requests.post(self.azure_url, headers=self.headers, json=body)
            request = await loop.run_in_executor(executor, post)
        response = request.json()
        response = response[0]['translations'][0]['text']
        translation = response

        screen_name = self.user_ids[tweet.user.id]
        url = f'https://twitter.com/{screen_name}/status/{tweet.id_str}'
        
        final_message = f'{translation}\n{url}'
        await self.channel.send(final_message)
        
    def cog_unload(self):
        print('Ending Twitter stream...')
        self.stream.disconnect()
        super().cog_unload()

class TweetListener(tweepy.StreamListener):
    def __init__(self, api, bot, cog, user_ids):
        self.api = api
        self.bot = bot
        self.cog = cog
        self.user_ids = user_ids

    def on_status(self, tweet):
        if tweet.user.id in self.user_ids and self.cog.channel:
            asyncio.run_coroutine_threadsafe(self.cog.send_tweet(tweet), self.bot.loop)

    def on_error(self, status_code):
        print(f'Error: {status_code}')
        return True

    def on_exception(self, exception):
        print(f'Exception: {exception}')
        self.cog.restart_stream()
        

def setup(bot):
    cfg = Config.get_data()
    bot.add_cog(TwitterCog(bot, cfg['twitter_ext']))
    print('Twitter extension loaded.')
