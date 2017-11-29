import asyncio
import configparser
import inspect
import sys
import time
import os
import platform
import discord
from discord.ext import commands
from logbook import Logger, StreamHandler, FileHandler

logger = Logger("Discord Music")
logger.handlers.append(StreamHandler(sys.stdout, bubble=True))
logger.handlers.append(FileHandler("last-run.log", bubble=True, mode="w"))

logger.debug("Loading config files")

default_config = "[Config]\n;Command prefix used by the 'Music Bee Now Playing' bot\n;def: dms.\ncommandPrefix = dms.\n\n;Whether the targeted user is a bot or a client (also, called self-bot)\n;The latter is technically against Discord's TOS. USE AT YOUR OWN RISK\n;def: true\nbot = true\n\n;Token of the client or bot you want to change the 'playing' status of\n;def: \ntoken = \n\n;Path to the text file you want to load your status message from\n;def: \npath = \n\n;Minimum length of the contents of the message file. If less, the file will be considered empty, as if no song is playing.\n;def: 10\nminLength = 10"

config = configparser.ConfigParser()

#config entries
commandPrefix = ""
isBot = True
token = ""
path = ""
minLength = 0

#loading config
if os.path.exists("config.ini"):
    config.read("config.ini")

    #commandPrefix
    try:
        commandPrefix = config['Config']['commandPrefix']
    except KeyError:
        logger.critical("No commandPrefix found in config, please ensure that the config formatting is correct")
        time.sleep(5)
        exit(1)

    if commandPrefix == "":
        logger.critical("No commandPrefix set! Exiting")
        time.sleep(5)
        exit(1)
        exit(1)

    #isBot
    try:
        isBot = config.getboolean('Config', 'bot')
    except KeyError:
        logger.critical("No bot found in config, please ensure that the config formatting is correct")
        time.sleep(5)
        exit(1)

    #token
    try:
        token = config['Config']['token']
    except KeyError:
        logger.critical("No token found in config, please ensure that the config formatting is correct")
        time.sleep(5)
        exit(1)

    if token == "":
        logger.critical("No token set! Exiting")
        time.sleep(5)
        exit(1)

    #path
    try:
        path = config['Config']['path']
    except KeyError:
        logger.critical("No path to file found in config, please ensure that the config formatting is correct")
        time.sleep(5)
        exit(1)

    if path == "":
        logger.critical("No path set! Exiting")
        time.sleep(5)

    #minLength
    try:
        minLength = config.getint('Config', 'minLength')
    except KeyError:
        logger.critical("No minimum file-length found in config, please ensure that the config formatting is correct")
        time.sleep(5)
        exit(1)
        minLength

else:
    logger.error("No config file, creating one now")
    with open("config.ini", 'w') as f:
        f.write(default_config)
    logger.info("Config created, please set config!")
    time.sleep(3)
    exit(0)

logger.info("Config loaded")

bot = commands.Bot(command_prefix=[commandPrefix], self_bot= not isBot)
bot.remove_command('help')


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} with ID {bot.user.id}")
    logger.info("Ready to start")


@bot.command(name="quit")
async def _quit():
    await bot.say("Logging out...")
    logger.info("Logging out")
    await bot.logout()
    exit(0)


def modification_date(path_to_file):
    if platform.system() == 'Windows':
        return os.path.getmtime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_mtime
        except AttributeError:
            return stat.st_birthtime


async def music_loop():
    await bot.wait_until_ready()
    await asyncio.sleep(1)
    last_song = ""
    timeLastModified = 0
    while not bot.is_closed:
        newTimeLastModified = modification_date(path)
        if timeLastModified != newTimeLastModified:
            timeLastModified = newTimeLastModified
            song = pull_song(path)
            if song != last_song:
                last_song = song
                if song == "" or len( song ) < minLength:
                    await bot.change_presence(afk=True, status=discord.Status.invisible, game=None)
                    logger.info("Cleared Discord Status because no song is playing")
                else:
                    await bot.change_presence(
                        afk=True,
                        status=discord.Status.idle,
                        game=discord.Game(name=song, type=2)
                        )
                    logger.info(f"Set Discord status to: Listening to {song.encode('ascii', 'ignore').decode()}")
        await asyncio.sleep(8)


def pull_song(path_to_file):
    with open(path_to_file, encoding="utf-8") as f:
        return f.read()


try:
    logger.info("Logging in")
    bot.loop.create_task(music_loop())
    bot.run(token, bot=isBot)
except discord.errors.LoginFailure:
    logger.critical("Log in failed, check token!")
    time.sleep(5)
    exit(1)
