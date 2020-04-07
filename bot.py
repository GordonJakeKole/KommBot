from discord.ext import commands
import json

config = open('cfg.json')
data = json.load(config)
token = data['token']

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print(f'Connection established.')

@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)

bot.run(token)
