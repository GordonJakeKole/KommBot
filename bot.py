from discord.ext import commands
import Utils.Config as Config

data = Config.get_data()
token = data['discord_token']
bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print(f'Connection established.')


extensions = data['extensions']
for extension in extensions:
    bot.load_extension(f'Extensions.{extension}')

bot.run(token)
