from pydoc import describe
import discord

bot = discord.Bot()

@bot.event
async def on_ready():
    print("Bot is ready!")

@bot.slash_command(name = "ping", description = "Pong!")
async def ping(ctx):
    embed = discord.Embed(title = "Pong!", color = 0x00ff00)
    embed.add_field(name = "Alice is gae", value = "Alice is gae", inline = False)
    await ctx.respond(embed = embed)

bot.run("OTg0NDYxMTg5NzA0NzMyNzIy.Gm6CUC._1GLIbzS6D_glNLNWQm5-Vvrd-cL9tC34nbEMk")
