from discord.ext import commands
#imports for twitter
import tweepy, asyncio
#imports for azure
import concurrent, requests, uuid, json

class TwitterCog(commands.Cog):
    def __init__(self, bot, cfg):
        self.bot = bot
        self.get_twitter_api(cfg)
        self.accounts = cfg['accounts']
        self.azure_setup(cfg)
        self.channels = set()
        self.start_twitter()

    def get_twitter_api(self, cfg):
        twitter_data = cfg['twitter']
        consumer_key = twitter_data['consumer_key']
        consumer_key_secret = twitter_data['consumer_key_secret']
        access_token = twitter_data['access_token']
        access_token_secret = twitter_data['access_token_secret']

        auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def start_twitter(self):
        acct_names = list(self.accounts.keys())
        try:
            users = self.api.lookup_users(screen_names=acct_names)
        except TweepError as e:
            print(f'Exception {e}.\nRestart required.')
            return
        _user_ids = dict()
        for user in users:
            s_name = user.screen_name
            _user_ids[user.id_str] = (s_name, tuple(self.accounts[s_name]))
        self.user_ids = _user_ids
        my_listener = TweetListener(self.api, self.bot, self, self.user_ids)
        self.stream = tweepy.Stream(auth=self.api.auth, listener=my_listener, daemon=True)
        self.start_stream()

    def azure_setup(self, cfg):
        azure_data = cfg['azure']
        translate_key = azure_data['translate_key']
        self.translate_endpoint = azure_data['translate_endpoint']
        self.headers = {
            'Ocp-Apim-Subscription-Key': translate_key,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        self.languages = azure_data['languages']
        self.dynamic_dict = azure_data['dynamic_dict']

    def start_stream(self):
        self.stream.disconnect()
        self.stream.filter(follow=list(self.user_ids.keys()), is_async=True, stall_warnings=True)

    @commands.group(help='Every twitter-related command begins with .twitter')
    async def twitter(self, ctx):
        pass

    @commands.is_owner()
    @commands.cooldown(rate=1, per=120)
    @twitter.command(name='restart', help='Refresh everything. Only usable by Komm.')
    async def twitter_restart(self, ctx):
        self.stream.disconnect()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            loop = asyncio.get_event_loop()
            start = lambda: self.start_twitter()
            request = await loop.run_in_executor(executor, start)
        twitters = list(self.accounts.keys())
        message = ', '.join(twitters)
        await ctx.send(f'Stream restarted. Now watching {message}')

    @twitter.group(name='check', help='Check input/output status and accounts followed.')
    async def twitter_check(self, ctx):
        if ctx.invoked_subcommand is None:
            twitters = list(self.user_ids.values())
            curr = [twitter[0] for twitter in twitters]
            curr = ', '.join(curr)
            await ctx.send(f'Stream Running: {self.stream.running}\n'
                           f'Channel Set: {len(self.channels) > 0}\n'
                           f'Currently following: {curr}\n')

    @twitter_check.command(name='future', help='Check followed account after restart.')
    async def twitter_check_future(self, ctx):
        twitters = list(self.accounts.keys())
        future = ', '.join(twitters)
        await ctx.send(f'Future following: {future}')

    @twitter.group(name='add', help='Add a channel or a Twitter account.')
    async def twitter_add(self, ctx):
        pass

    @twitter_add.command(name='channel')
    async def twitter_add_channel(self, ctx):
        if ctx.channel not in self.channels:
            self.channels.add(ctx.channel)
        await ctx.send('Sending tweets here.')

    @twitter_add.command(name='account')
    async def twitter_add_account(self, ctx, account_name, *args):
        for language in args:
            if language not in self.languages:
                await ctx.send('Invalid language. Review docs.microsoft.com/en-us/azure/cognitive-services/translator/language-support')
                return
        if len(args) == 0:
            self.accounts[account_name] = ()
        elif len(args) == 1:
            self.accounts[account_name] = (args[0])
        else:
            self.accounts[account_name] = (args[0], args[1])

    @twitter.group(name='delete', help='Delete a channel or Twitter account.')
    async def twitter_delete(self, ctx):
        pass

    @twitter_delete.command(name='channel')
    async def twitter_delete_channel(self, ctx):
        if ctx.channel in self.channels:
            self.channels.remove(ctx.channel)
        await ctx.send('Not sending tweets here.')

    @twitter_delete.command(name='account')
    async def twitter_delete_account(self, ctx, account_name):
        try:
            self.accounts.pop(account_name)
        except KeyError as e:
            return

    async def send_tweet(self, tweet):
        s_name, languages = self.user_ids[tweet.user.id_str]
        if len(languages) == 0:
            translate, og_lang, new_lang = False, None, None
        elif len(languages) == 1:
            translate, og_lang, new_lang = True, None, languages[0]
        elif len(languages) == 2:
            translate, og_lang, new_lang = True, languages[0], languages[1]
        
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

        url = f'https://twitter.com/{s_name}/status/{tweet.id_str}'
        if not translate:
            final_message = f'{tweet_text}\n{url}'
        else:
            tweet_text = tweet_text.replace('#', '# ')
            for original, translation in self.dynamic_dict.items():
                tweet_text = tweet_text.replace(original, f'<mstrans:dictionary translation="{translation}">{original}</mstrans:dictionary>')

            body = [{
                'text' : tweet_text
            }]
            if og_lang:
                params = f'&from={og_lang}&to={new_lang}'
            else:
                params = f'&to={new_lang}'
            azure_url = self.translate_endpoint + params
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                loop = asyncio.get_event_loop()
                post = lambda: requests.post(azure_url, headers=self.headers, json=body)
                request = await loop.run_in_executor(executor, post)
            response = request.json()
            response = response[0]['translations'][0]['text']
            translation = response
            
            final_message = f'{translation}\n{url}'
            
        for channel in self.channels:
            await channel.send(final_message)
        
    def cog_unload(self):
        self.stream.disconnect()
        super().cog_unload()

class TweetListener(tweepy.StreamListener):
    def __init__(self, api, bot, cog, user_ids):
        self.api = api
        self.bot = bot
        self.cog = cog
        self.user_ids = user_ids

    def on_status(self, tweet):
        if tweet.user.id_str in self.user_ids and self.cog.channels:
            asyncio.run_coroutine_threadsafe(self.cog.send_tweet(tweet), self.bot.loop)

    def on_error(self, status_code):
        print(f'Error: {status_code}')
        return True

    def on_exception(self, exception):
        print(f'Exception: {exception}')
        print('Restarting Twitter stream...')
        self.cog.start_stream()
        

def setup(bot):
    with open('Extensions/twitter/twitter.json', encoding='utf-8') as config:
        data = json.load(config)
    bot.add_cog(TwitterCog(bot, data))
