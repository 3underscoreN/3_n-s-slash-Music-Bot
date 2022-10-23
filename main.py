import logging
import discord
import orjson
import os

OWNER = int(os.getenv('OWNER'))

bot = discord.Bot()
logging.basicConfig(
    filename = "botLog.log", 
    level = logging.INFO, 
    format = "%(asctime)s %(levelname)s: %(message)s", 
    datefmt = '%m/%d/%Y %I:%M:%S %p'
)
with open("./Botcommands/commandList.json") as f:
    COMMANDS = orjson.loads(f.read())
COMMANDS_UNPACKED = []
for category in COMMANDS:
    for command in COMMANDS[category]:
        COMMANDS_UNPACKED.append(command)

@bot.event
async def on_ready():
    print("Bot is ready!")

@bot.slash_command(name = "ping", description = "Fetches bot latency.")
async def ping(ctx):
    embed = discord.Embed(title = "Pong!", color = 0x00ff00)
    embed.add_field(name = f"Latency: `{round(bot.latency * 1000)}ms`", value = "If you experience delays in command, the bot might have internal error.", inline = False)
    embed.set_footer(text = "ping · Bot made by 3_n$7069")
    await ctx.respond(embed = embed)

@bot.slash_command(name = "shutdown", description = "Shuts down the bot.") # This is a command that only the owner can use.
async def shutdown(ctx):
    if ctx.author.id == OWNER:
        embed = discord.Embed(title = "Success", color = 0x00ff00)
        embed.add_field(name = "Shutting down", value = "The bot is now shutting down.")
        embed.set_footer(text = "Shutdown · Bot made by 3_n#7069")
        await ctx.respond(embed = embed)
        print("Shutting down...")
        ctx.voice_client.disconnect()
        await bot.close()
    else:
        embed = discord.Embed(title = "Error: Not Owner", color = 0xff0000)
        embed.add_field(name = "You cannot use the command.", value = "Only owner can use this command.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", inline = False)
        embed.set_footer(text = "shutdown · Bot made by 3_n#7069")
        await ctx.respond(embed = embed)
        logging.warn("Bot shutdown command was used by non-owner.")

@bot.slash_command(name = "about", description = "Shows information about the bot.")
async def about(ctx):
    embed = discord.Embed(title = "About", description = "Bot written by 3_n with ❤️", color = 0x00f552)
    embed.add_field(name = "Special Thanks", value = "Alex (horny guy), Leo (so sad), Eugene (not paramount)\n * For giving me inspiration to write this bot", inline = False)
    embed.add_field(name = "Issues and contributions", value = "You can always contribute by opening issues and/or pull requests. Click [here](https://github.com/3underscoreN/3_n-s-slash-Music-Bot) to visit repo page.", inline = False)
    embed.set_footer(text = "about · Bot made by 3_n#7069")
    await ctx.respond(embed = embed)

@bot.slash_command(name = "sysrun", description = "For debugging purpose only. runs a specific python statement.")
@discord.option("command", str, description = "Wrapped in print() for output. Supports variable-only statements and expression only.")
async def sysrun(ctx, command:str):
    if ctx.author.id == OWNER:
        try:
            exec(f'print({command})')
            embed = discord.Embed(title = "Success", color = 0x00ff00)
            embed.add_field(name = "Your instruction has been executed.",value = "Please check output in the console.", inline = False)
            embed.set_footer(text = "sysrun · Bot made by 3_n#706")
        except Exception as e:
            embed = discord.Embed(title = "Error", color = 0xff0000)
            embed.add_field(name = "Your instruction has NOT been executed.", value = f"There is an error in running your command.\nOriginal message: `{repr(e)}`", inline = False)
    else:
        embed = discord.Embed(title = "Error: Not Owner", color = 0xff0000)
        embed.add_field(name = "You cannot use the command.", value = "Only owner can use this command.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", inline = False)
        embed.set_footer(text = "shutdown · Bot made by 3_n#7069")
        logging.warn("Bot sysrun command was used by non-owner.")
    await ctx.respond(embed = embed)

@bot.slash_command(name = "help", description = "Shows a list of commands when nothing is passed, and shows a specific information if one is passed.")
@discord.option("command", description = "A speicific command", required = False, choices = COMMANDS_UNPACKED)
async def help(ctx, command:str):
    print(COMMANDS)
    print(COMMANDS_UNPACKED)
    await ctx.respond("Help command is not yet implemented.")

bot.load_extension("music")

if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'))
    print("Shutdown complete!")
