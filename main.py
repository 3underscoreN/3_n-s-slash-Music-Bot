import logging
from ssl import Options
import discord
import os
import music

OWNER = int(os.getenv('OWNER'))
class notOwner(Exception):
    pass

bot = discord.Bot()
logging.basicConfig(
    filename = "botLog.log", 
    level = logging.INFO, 
    format = "%(asctime)s %(levelname)s: %(message)s", 
    datefmt = '%m/%d/%Y %I:%M:%S %p'
)

cogs = [music.music()]
for i in range(len(cogs)):
    cogs[i].setup(bot)

@bot.event
async def on_ready():
    print("Bot is ready!")

@bot.slash_command(name = "ping", description = "Fetches bot latency.")
async def ping(ctx):
    embed = discord.Embed(title = "Pong!", color = 0x00ff00)
    embed.add_field(name = f"Latency: `{round(bot.latency * 1000)}ms`", value = "If you experience delays in command, the bot might have internal error.", inline = False)
    await ctx.respond(embed = embed)

@bot.slash_command(name = "shutdown", description = "Shuts down the bot.", permission_number = OWNER)
async def shutdown(ctx):
    if ctx.author.id == OWNER:
        await ctx.respond("Shutting down... Check console!")
        print("Shutting down...")
        await bot.close()
        print("Shutdown complete!")
    else:
        raise notOwner

@bot.event
async def on_error(ctx, error):
    if isinstance(error, notOwner):
        await ctx.respond("You are not the owner of this bot!")
    else:
        await ctx.respond(f"An error occured! Error: {error}")

bot.run(os.getenv('TOKEN'))
