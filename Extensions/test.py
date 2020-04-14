from discord.ext import commands
import random

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def echo(self, ctx, *, msg):
        """Have the bot repeat what you just said"""
        await ctx.send(msg)

    @commands.command()
    async def roll(self, ctx, A: int, X: int):
        """Roll an AdX die"""
        rolls = sorted([random.randint(1, X) for _ in range(A)])
        await ctx.send(', '.join(str(roll) for roll in rolls))
    
    @commands.command()
    async def hello(self, ctx):
        """Says hello"""
        await ctx.send('Hello')

def setup(bot):
    bot.add_cog(TestCog(bot))
    print('Test extension loaded.')
