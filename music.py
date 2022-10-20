import discord

class music(discord.Cog):

    @discord.slash_command(name = "anotherping", description = "Another Pong but you have to pass in an argument!")
    async def ping2(self, ctx, string:str):
        await ctx.respond(f"Pong! You passed in {string}!")

    def setup(self, bot):
        bot.add_cog(music(bot))

if __name__ == "__main__":
    print("This is not the main script! Run main.py!")