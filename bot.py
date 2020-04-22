import discord
from discord.ext import commands
import Utils.Config as Config

data = Config.get_data()
token = data['discord_token']
bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    activity = discord.Activity(name='C2 Twitter', type=discord.ActivityType.watching)
    await bot.change_presence(activity=activity)
    print(f'KommBot is a go.')

extensions = data['extensions']
for extension in extensions:
    bot.load_extension(f'Extensions.{extension}')

bot.run(token)
