import discord
from discord.ext import commands
import pafy
import logging
import re
from youtube_search import YoutubeSearch
import os
import datetime

OWNER = int(os.getenv("OWNER"))

# regex that matches youtube url with video id
YOUTUBE_REGEX = re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.{11})")
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class queue():
    def __init__(self):
        self.queue = []
        self.current = None

    def add(self, pafyObject, requester):
        self.queue.append([pafyObject, requester])
        return len(self.queue)

    def next(self):
        self.current = self.queue.pop(0)
        return self.current

    def remove(self, index):
        return self.queue.pop(index)

    def reset(self):
        self.queue = []
        self.current = None

    def length(self):
        return len(self.queue)

songQueue = queue()
    

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def playnext(self, ctx):
        if songQueue.length() == 0:
            songQueue.reset()
            return
        song = songQueue.next()
        ctx.voice_client.play(discord.FFmpegOpusAudio(song[0].getbestaudio().url, **FFMPEG_OPTIONS), after=lambda e: self.playnext(ctx))

    @commands.slash_command(name = "musicsysrun", description = "Runs a simple command in music.py. Used for debugging.")
    async def musicsysrun(self, ctx, command:str):
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

    @commands.slash_command(name = "join", description = "Joins the voice channel you are in.")
    async def join(self, ctx):
        try:
            if ctx.author.voice is None:
                embed = discord.Embed(title = "Error: Not in voice channel", color = 0xff0000)
                embed.add_field(name = "You are not in a voice channel.", value = "Please join a voice channel and try again.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", inline = False)
                embed.set_footer(text = "join · Bot made by 3_n#7069")
                await ctx.respond(embed = embed)
                logging.warn(f"{ctx.author} tried to run /join but was not in any voice channel.")
            else:
                await ctx.author.voice.channel.connect()
                embed = discord.Embed(title = "Success", color = 0x00ff00)
                embed.add_field(name = "Joined Voice Channel", value = f"Joined `{ctx.author.voice.channel.name}`. Feel free to play music with `/play` now~", inline = False)
                embed.set_footer(text = "join · Bot made by 3_n#7069")
                await ctx.respond(embed = embed)
        except discord.errors.ClientException:
            embed = discord.Embed(title = "Error: Already in voice channel", color = 0xff0000)
            embed.add_field(name = "It looks like I am in another voice channel.", value = f"Maybe you can try to move to that {ctx.voice_client.channel}.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", inline = False)
            embed.set_footer(text = "join · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)
            logging.warn(f"{ctx.author} tried to run /join but the bot is already in {ctx.voice_client.channel}.")

    @commands.slash_command(name = "leave", description = "Leaves the voice channel you are in.")
    async def leave(self, ctx):
        try:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                await ctx.voice_client.disconnect()
                songQueue.reset()
                embed = discord.Embed(title = "Success", color = 0x00ff00)
                embed.add_field(name = "Left Voice Channel", value = f"Left `{ctx.author.voice.channel.name}`. You can always do `/join` to get me back in!", inline = False)
                embed.set_footer(text = "leave · Bot made by 3_n#7069")
                await ctx.respond(embed = embed)
            else:
                embed = discord.Embed(title = "Error: Not in same voice channel", color = 0xff0000)
                embed.add_field(name = "Not in same voice channel", value = f"It looks like you are not in the same voice channel as me.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot)." , inline = False)
                embed.set_footer(text = "leave · Bot made by 3_n#7069")
                await ctx.respond(embed = embed)
                logging.warn(f"{ctx.author} tried to run /leave but is not in the same voice channel as the bot.")
        except AttributeError:
            embed = discord.Embed(title = "Error: Not in voice channel", color = 0xff0000)
            embed.add_field(name = "It looks like I am not in any voice channels.", value = f"If I am not in any voice channel, I can't leave any voice channels!\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", inline = False)
            embed.set_footer(text = "leave · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)
            logging.warn(f"{ctx.author} tried to run /leave but the bot is not in any voice channel.")

    @commands.slash_command(name = "play", description = "Plays a song from YouTube.")
    @discord.option("url_or_keyword", str, description = "The song you want to play, either in URL or in keyword", required = True)
    async def play(self, ctx, url_or_keyword:str):
        global songQueue
        embed = discord.Embed(title = "Loading...", color = 0x0000ff)
        embed.add_field(name = "Please wait while the command is being processed...", value = "This may take a while. If you found it stuck in this dialog, there might be an internal error. Please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot) if you do think something's wrong.", inline = False)
        embed.set_footer(text = "play · Bot made by 3_n#7069")
        message = await ctx.respond(embed = embed)

        # join the voice channel if the bot is not in any voice channel
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        # check if the input is a URL or a keyword
        url = YOUTUBE_REGEX.match(url_or_keyword)
        if url:
            url = url.group(0)
        else:
            url = "https://www.youtube.com" + YoutubeSearch(url_or_keyword, max_results = 1).to_dict()[0]["url_suffix"]
        
        # try to get the video. 
        # The reason why the code is protected is because the bot may not be able to get the video (e.g. private videos)
        try:
            item = pafy.new(url)
        except ValueError:
            embed = discord.Embed(title = "Error: Invalid Video", color = 0xff0000)
            embed.add_field(name = "The video you provided is invalid.", value = "Please make sure you are providing a valid video URL or a valid keyword.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", inline = False)
            embed.set_footer(text = "play · Bot made by 3_n#7069")
            await message.edit_original_response(embed = embed)
            logging.warn(f"{ctx.author} tried to run /play but provided an invalid video URL or keyword.")
            return
        
        # play the song
        if ctx.voice_client.is_playing():
            queuePos = songQueue.add(item, ctx.author)
            embed = discord.Embed(title = "Success", color = 0x00ff00)
            embed.add_field(name = "Added to queue", value = f"Your song `{item.title}` has been added with a position of `{queuePos}`.", inline = False)
            embed.set_thumbnail(url = item.thumb)
            embed.set_footer(text = "play · Bot made by 3_n#7069")
            await message.edit_original_response(embed = embed)
        else:
            songQueue.current = [item, ctx.author]
            source = discord.FFmpegOpusAudio(item.getbestaudio().url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after = lambda e: self.playnext(ctx))
            embed = discord.Embed(title = "Success", color = 0x00ff00)
            embed.add_field(name = "Now playing", value = f"Your song `{item.title}` should be played instantly.", inline = False)
            embed.set_thumbnail(url = item.thumb)
            embed.set_footer(text = "play · Bot made by 3_n#7069")
            await message.edit_original_response(embed = embed)

    @commands.slash_command(name = "queue", description = "Shows the current queue.")
    async def queue(self, ctx):
        global songQueue
        if songQueue.current is None:
            embed = discord.Embed(title = "Error: No songs in queue", color = 0xff0000)
            embed.add_field(name = "There are no songs in the queue.", value = "Please play a song first before checking the queue.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot)." , inline = False)
            embed.set_footer(text = "queue · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)
            logging.warn(f"{ctx.author} tried to run /queue but there are no songs in the queue.")
        else:
            embed = discord.Embed(title = "Queue", color = 0x00f552)
            embed.add_field(name = "Now playing", value = f"[{songQueue.current[0].title}](https://youtube.com/watch?v={songQueue.current[0].videoid})\nDuration: {songQueue.current[0].duration}\nRequested by {songQueue.current[1].mention}", inline = False)
            embed.set_footer(text = "queue · Bot made by 3_n#7069")
            if songQueue.length() > 0:
                embed.add_field(
                    name = "Up next", 
                    value = "\n\n".join([f"**{i + 1}**: [{songQueue.queue[i][0].title}](https://youtube.com/watch?v={songQueue.queue[i][0].videoid})\nDuration: {songQueue.queue[i][0].duration}\nRequested by: {songQueue.queue[i][1].mention}" for i in range(songQueue.length())]), 
                    inline = False
                )
                total_queue_length = sum([songQueue.queue[i][0].length for i in range(songQueue.length())])
                embed.set_footer(text = f"queue · Total queue length: {str(datetime.timedelta(seconds = total_queue_length))} · Bot made by 3_n#7069 ")
            await ctx.respond(embed = embed)
    
    @commands.slash_command(name = "skip", description = "Skips a specific song in the queue. If no index is provided, the bot will skip the current song.")
    @discord.option("index", int, description = "The index of the song you want to skip.", required = False)
    async def skip(self, ctx, index:int):
        global songQueue
        if songQueue.current is None:
            embed = discord.Embed(title = "Error: No songs in queue", color = 0xff0000)
            embed.add_field(name = "There are no songs in the queue.", value = "Please play a song first before skipping.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot)." , inline = False)
            embed.set_footer(text = "skip · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)
            logging.warn(f"{ctx.author} tried to run /skip but there are no songs in the queue.")
        elif index is None:
            ctx.voice_client.stop()
            embed = discord.Embed(title = "Success", color = 0x00ff00)
            embed.add_field(name = "Skipped", value = f"The currently playing song has been skipped.", inline = False)
            embed.set_footer(text = "skip · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)
        elif index < 1 or index > songQueue.length():
            embed = discord.Embed(title = "Error: Invalid index", color = 0xff0000)
            embed.add_field(name = "The index you provided is invalid.", value = "Please make sure you are providing a valid index.\nIf you believe this is an error, please open an issue on [GitHub](https://githubcom/3underscoreN/3_n-s-slash-Music-Bot)." , inline = False)
            embed.set_footer(text = "skip · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)
            logging.warn(f"{ctx.author} tried to run /skip but provided an invalid index.")
        else:
            RemovedSong = songQueue.remove(index - 1)
            embed = discord.Embed(title = "Success", color = 0x00ff00)
            embed.add_field(name = "Skipped", value = f"The song at index `{index}`,  {RemovedSong[0].title} has been skipped.", inline = False)
            embed.set_footer(text = "skip · Bot made by 3_n#7069")
            await ctx.respond(embed = embed)

def setup(bot):
    bot.add_cog(music(bot))

if __name__ == "__main__":
    print("This is not the main script! Run main.py!")