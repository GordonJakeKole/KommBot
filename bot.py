import discord
from discord.ext import commands
import json

def main():
    with open('cfg.json') as config:
        try:
            data = json.load(config)
        except:
            print('cfg.json failed to load. Bot cannot start.')
            return

    token = data['discord_token']
    prefix = data['command_prefix']
    bot = commands.Bot(command_prefix=prefix)

    extensions = data['extensions']
    for extension in extensions:
        try:
            bot.load_extension(f'Extensions.{extension}.{extension}')
        except Exception as e:
            print(f'{extension} extension failed to load. Exception: {e}')

    bot.run(token)

if __name__ == '__main__':
    main()
