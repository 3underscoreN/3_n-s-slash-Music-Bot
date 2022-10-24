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

class embedPackaging():

    @staticmethod
    async def packEmbed(**kwargs):
        """
        Packs a ``discord.Embed()`` object with the given parameters, along with a footer for this bot.
        
        This function only accepts keyword arguments listed below.

        This function is a coroutine and must be awaited.

        Parameters
        ----------
        title : str
            Required. The title of the embed. Same as the ``title`` keyword argument in ``discord.Embed()``.

        description : str
            Optional. The description of the embed. Same as the ``description`` keyword argument in ``discord.Embed()``.

        embedType : str
            Optional. The color of the embed. Can be "success", "error", or "info". 
            "success" is green, "error" is red, and "info" is the color ``0x11f1f5``.

        color : Union[int, discord.Color]
            Optional. The color of the embed. Same as the ``color`` keyword argument in ``discord.Embed()``.
            If both embedType and color are given, embedType will be used and color will be ignored.

        fields : list
            Optional. A list of fields to add to the embed. Same as the ``add_field()`` method in ``discord.Embed()``.
            Each field must be a ``dict`` with all the keys needed for calling ``discord.Embed().add_field()`` method.

        Returns
        -------
        class:`discord.Embed`
            The embed object with the given parameters.
        """
        colors = { # for embedType
            "success": 0x00ff00,
            "error": 0xff0000,
            "info": 0x11f1f5
        }

        Rembed = discord.Embed(title = kwargs["title"], description = kwargs.get("description"), color = colors.get(kwargs.get("embedType")) or kwargs.get("color") or 0x000000) 
        for field in (kwargs.get("fields") or {}):
            Rembed.add_field(**field)
        if (command := kwargs.get("command")) != None:
            Rembed.set_footer(text = f"{command} · Bot made by 3_n#7069")
        else:
            Rembed.set_footer(text = "Bot made by 3_n#7069")

        return Rembed

@bot.event
async def on_ready():
    print("Bot is ready!")

@bot.slash_command(name = "ping", description = "Fetches bot latency.")
async def ping(ctx):
    embed = await embedPackaging.packEmbed(
        title = "Pong!",
        embedType = "info",
        command = "ping",
        fields = [
            {"name": "Latency:", "value": f"`{round(bot.latency * 1000)}ms`", "inline": False}
        ]
    )
    await ctx.respond(embed = embed)

@bot.slash_command(name = "shutdown", description = "Shuts down the bot.") # This is a command that only the owner can use.
async def shutdown(ctx):
    if ctx.author.id == OWNER:
        embed = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "shutdown",
            fields = [
                {"name": "Shutting down...", "value": "The bot is now shutting down.", "inline": False}
            ]
        )
        print("Shutting down...")
        await ctx.voice_client.disconnect()
        await ctx.respond(embed = embed)
        await bot.close()
    else:
        embed = await embedPackaging.packEmbed(
            title = "Error: Not Owner",
            embedType = "error",
            command = "shutdown",
            fields = [
                {"name": "You cannot use the command.", "value": "Only owner can use this command.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
            ]
        )
        await ctx.respond(embed = embed, ephemeral = True)
        logging.warn("Bot shutdown command was used by non-owner.")

@bot.slash_command(name = "about", description = "Shows information about the bot.")
async def about(ctx):
    embed = await embedPackaging.packEmbed(
        title = "About",
        description = "Bot written by 3_n with ❤️",
        embedType = "info",
        command = "about",
        fields = [
            {"name": "Special Thanks", "value": "Alex (horny guy), Leo (so sad), Eugene (not paramount)\n * For giving me inspiration to write this bot", "inline": False},
            {"name": "Issues and contributions", "value": "You can always contribute by opening issues and/or pull requests. Click [here](https://github.com/3underscoreN/3_n-s-slash-Music-Bot) to visit repo page.", "inline": False}
        ]
    )
    await ctx.respond(embed = embed)

@bot.slash_command(name = "sysrun", description = "For debugging purpose only. runs a specific python statement.")
@discord.option("command", str, description = "Wrapped in print() for output. Supports variable-only statements and expression only.")
async def sysrun(ctx, command:str):
    if ctx.author.id == OWNER:
        try:
            exec(f'print({command})')
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "sysrun",
                fields = [
                    {"name": "Your instruction has been executed.", "value": "Please check output in the console.", "inline": False}
                ]
            )
        except Exception as e:
            embed = await embedPackaging.packEmbed(
                title = "Error",
                embedType = "error",
                command = "sysrun",
                fields = [
                    {"name": "Your instruction has NOT been executed.", "value": f"There is an error in running your command.\nOriginal message: `{repr(e)}`", "inline": False}
                ]
            )
    else:
        embed = await embedPackaging.packEmbed(
            title = "Error: Not Owner",
            embedType = "error",
            command = "sysrun",
            fields = [
                {"name": "You cannot use the command.", "value": "Only owner can use this command.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline":False}
            ]
        )
        logging.warn("Bot sysrun command was used by non-owner.")
    await ctx.respond(embed = embed, ephemeral = True)

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
