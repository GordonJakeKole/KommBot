import discord
from discord.ext import commands

class BasicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        my_activity = discord.Activity(name='C2 Twitter', type=discord.ActivityType.watching)
        await self.bot.change_presence(activity=my_activity)
        print('Kommbot is a go!')

    @commands.command(name='about', help='Learn about the bot.')
    async def about_the_bot(self, ctx):
        await ctx.send('KommBot was created out of boredom by Komm. '
                       'Its main purpose is to post translated tweets right into Discord.')

    @commands.is_owner()
    @commands.command(name='reload_ext', help='Reload an extension. Only usable by Komm.')
    async def reload_extension(self, ctx, ext):
        try:
            self.bot.reload_extension(f'Extensions.{ext}.{ext}')
        except:
            await ctx.send('Reload failed.')
        else:
            await ctx.send(f'Extension {ext} reloaded successfully.')

    @commands.is_owner()
    @commands.group(help='Set the status of the bot. Only usable by Komm.')
    async def status(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid activity.')
        else:
            await ctx.send('Status changed.')

    @status.command()
    async def playing(self, ctx, *, activity_name):
        my_activity = discord.Game(activity_name)
        await self.bot.change_presence(activity=my_activity)

    @status.command()
    async def streaming(self, ctx, activity_url, *, activity_name):
        my_activity = discord.Streaming(name=activity_name, url=activity_url)
        await self.bot.change_presence(activity=my_activity)

    @status.command()
    async def listening(self, ctx, *, activity_name):
        my_activity = discord.Activity(name=activity_name, type=discord.ActivityType.listening)
        await self.bot.change_presence(activity=my_activity)

    @status.command()
    async def watching(self, ctx, *, activity_name):
        my_activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
        await self.bot.change_presence(activity=my_activity)

def setup(bot):
    bot.add_cog(BasicCog(bot))
