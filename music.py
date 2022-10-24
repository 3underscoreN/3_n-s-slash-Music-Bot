import discord
from discord.ext import commands
from discord.ext.pages import Paginator, PaginatorButton
import pafy
import logging
import re
from youtube_search import YoutubeSearch
import os
import datetime
from main import embedPackaging

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

def playnext(ctx):
    if songQueue.length() == 0:
        songQueue.reset()
        return
    song = songQueue.next()
    ctx.voice_client.play(discord.FFmpegOpusAudio(song[0].getbestaudio().url, **FFMPEG_OPTIONS), after=lambda e: playnext(ctx))

class playButton(PaginatorButton):
    def __init__(self, ctx, result):
        super().__init__("page_indicator", style = discord.ButtonStyle.green)
        self.ctx = ctx
        self.result = result

    async def callback(self, interaction: discord.Interaction):
        index = self.paginator.current_page
        # plays the song (not using invoke(play) sice that pollutes stuff)
        url = "https://youtube.com" + self.result[index]["url_suffix"]
        item = pafy.new(url)
        if self.ctx.voice_client is None:
            await self.ctx.author.voice.channel.connect()

        if self.ctx.voice_client.is_playing():
            queuePos = songQueue.add(item, self.ctx.author)
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "play",
                fields = [
                    {"name": "Added to queue", "value": f"Your song `{item.title}` has been added with a position of `{queuePos}`.", "inline": False},
                    {"name": "Pro tip!", "value": "The buttons below can still be used to nevigete the search query.", "inline": False}
                ]
            )
        else:
            songQueue.current = [item, self.ctx.author]
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "play",
                fields = [
                    {"name": "Playing", "value": f"Now playing `{item.title}`.", "inline": False},
                    {"name": "Pro tip!", "value": "The buttons below can still be used to nevigete the search query.", "inline": False}
                ]
            )
            self.ctx.voice_client.play(discord.FFmpegOpusAudio(item.getbestaudio().url, **FFMPEG_OPTIONS), after = lambda e: playnext(self.ctx))
        await interaction.response.defer()
        await self.ctx.edit(embed = embed)


class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "musicsysrun", description = "Runs a simple command in music.py. Used for debugging.")
    async def musicsysrun(self, ctx, command:str):
        if ctx.author.id == OWNER:
            try:
                exec(f'print({command})')
                embed = await embedPackaging.packEmbed(
                    title = "Success",
                    embedType = "success",
                    command = "musicsysrun",
                    fields = [
                        {"name": "Your instruction has been executed.", "value": "Please check output in the console.", "inline": False}
                    ]
                )
            except Exception as e:
                embed = await embedPackaging.packEmbed(
                    title = "Error",
                    embedType = "error",
                    command = "musicsysrun",
                    fields = [
                        {"name": "Your instruction has NOT been executed.", "value": f"There is an error in running your command.\nOriginal message: `{repr(e)}`", "inline": False}
                    ]
                )
        else:
            embed = await embedPackaging.packEmbed(
                title = "Error: Not Owner",
                embedType = "error",
                command = "musicsysrun",
                fields = [
                    {"name": "You cannot use the command.", "value": "Only owner can use this command.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            logging.warn("Bot sysrun command was used by non-owner.")
        await ctx.respond(embed = embed, ephemeral = True)

    @commands.slash_command(name = "join", description = "Joins the voice channel you are in.")
    async def join(self, ctx):
        try:
            if ctx.author.voice is None:
                embed = await embedPackaging.packEmbed(
                    title = "Error: Not in voice channel",
                    embedType = "error",
                    command = "join",
                    fields = [
                        {"name": "You are not in a voice channel.", "value": "Please join a voice channel and try again.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed, ephemeral = True)
                logging.warn(f"{ctx.author} tried to run /join but was not in any voice channel.")
            else:
                await ctx.author.voice.channel.connect()
                embed = await embedPackaging.packEmbed(
                    title = "Success",
                    embedType = "success",
                    command = "join",
                    fields = [
                        {"name":"Joined Voice Channel", "value":f"Joined `{ctx.author.voice.channel.name}`. Feel free to play music with `/play` now~", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed)
        except discord.errors.ClientException:
            embed = await embedPackaging.packEmbed(
                title = "Error: Already in voice channel",
                embedType = "error",
                command = "join",
                fields = [
                    {"name": "It looks like I am in another voice channel.", "value": f"Maybe you can try to move to that {ctx.voice_client.channel}.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /join but the bot is already in {ctx.voice_client.channel}.")

    @commands.slash_command(name = "leave", description = "Leaves the voice channel you are in.")
    async def leave(self, ctx):
        try:
            if ctx.voice_client.channel == ctx.author.voice.channel:
                await ctx.voice_client.disconnect()
                songQueue.reset()
                embed = await embedPackaging.packEmbed(
                    title = "Success",
                    embedType = "success",
                    command = "leave",
                    fields = [
                        {"name": "Left Voice Channel", "value": f"Left `{ctx.author.voice.channel.name}` (by the way, I also cleared the current queue.). You can always do `/join` to get me back in!", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed)
            else:
                embed = await embedPackaging.packEmbed(
                    title = "Error: Not in same voice channel",
                    embedType = "error",
                    command = "leave",
                    fields = [
                        {"name": "Not in same voice channel", "value": f"It looks like you are not in the same voice channel as me.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed, ephemeral = True)
                logging.warn(f"{ctx.author} tried to run /leave but is not in the same voice channel as the bot.")
        except AttributeError: # if ctx.voice_client returns None
            embed = await embedPackaging.packEmbed(
                title = "Error: Not in voice channel",
                embedType = "error",
                command = "leave",
                fields = [
                    {"name": "It looks like I am not in any voice channels.", "value": f"If I am not in any voice channel, I can't leave any voice channels!\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot)." , "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /leave but the bot is not in any voice channel.")

    @commands.slash_command(name = "play", description = "Plays a song from YouTube.")
    @discord.option("url_or_keyword", str, description = "The song you want to play, either in URL or in keyword", required = True)
    async def play(self, ctx, url_or_keyword:str):
        global songQueue
        await ctx.defer()

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
            embed = await embedPackaging.packEmbed(
                title = "Error: Invalid Video",
                embedType = "error",
                command = "play",
                fields = [
                    {"name": "The video you provided is invalid.", "value": "Please make sure you are providing a valid video URL or a valid keyword.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            await ctx.send_followup(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /play but provided an invalid video URL or keyword.")
            return
        
        # attempts to play the song or add it to the queue
        if ctx.voice_client.is_playing(): # if the bot is playing a song, add the song to the queue
            queuePos = songQueue.add(item, ctx.author)
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "play",
                fields = [
                    {"name": "Added to queue", "value": f"Your song `{item.title}` has been added with a position of `{queuePos}`.", "inline": False}
                ]
            )
            embed.set_thumbnail(url = item.thumb)
            await ctx.send_followup(embed = embed)
        else: # if the bot is not playing anything, play the song
            songQueue.current = [item, ctx.author]
            source = discord.FFmpegOpusAudio(item.getbestaudio().url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after = lambda e: playnext(ctx))
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "play",
                fields = [
                    {"name": "Now playing", "value": f"Your song `{item.title}` should be played instantly.", "inline": False}
                ]
            )
            embed.set_thumbnail(url = item.thumb)
            await ctx.send_followup(embed = embed)

    @commands.slash_command(name = "queue", description = "Shows the current queue.")
    async def queue(self, ctx):
        global songQueue
        if songQueue.current is None:
            embed = await embedPackaging.packEmbed(
                title = "Error: No songs in queue",
                embedType = "error",
                command = "queue",
                fields = [
                    {"name": "There are no songs in the queue.", "value": "Please play a song first before checking the queue.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline":False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /queue but there are no songs in the queue.")
        else:
            embed = await embedPackaging.packEmbed(
                title = "Queue",
                embedType = "info",
                command = "queue",
                fields = [
                    {"name": "Now playing", "value": f"[{songQueue.current[0].title}](https://youtube.com/watch?v={songQueue.current[0].videoid})\nDuration: {songQueue.current[0].duration}\nRequested by {songQueue.current[1].mention}", "inline":False}
                ]
            )
            if songQueue.length() > 0:
                embed.add_field( # packEmbed returns a discord.Embed() object, so we can use the add_field() method!
                    name = "Up next", 
                    value = "\n\n".join([f"**{i + 1}**: [{songQueue.queue[i][0].title}](https://youtube.com/watch?v={songQueue.queue[i][0].videoid})\nDuration: {songQueue.queue[i][0].duration}\nRequested by: {songQueue.queue[i][1].mention}" for i in range(songQueue.length())]), 
                    inline = False
                )
                total_queue_length = sum([songQueue.queue[i][0].length for i in range(songQueue.length())])
                embed.set_footer(text = f"queue · Total queue length: {str(datetime.timedelta(seconds = total_queue_length))} · Bot made by 3_n#7069 ") # Overwrites the default footer
            await ctx.respond(embed = embed)
    
    @commands.slash_command(name = "skip", description = "Skips a specific song in the queue. If no index is provided, the bot will skip the current song.")
    @discord.option("index", int, description = "The index of the song you want to skip.", required = False, min_value = 1)
    async def skip(self, ctx, index:int):
        global songQueue
        if songQueue.current is None:
            embed = await embedPackaging.packEmbed(
                title = "Error: No songs in queue",
                embedType = "error",
                command = "skip",
                fields = [
                    {"name": "There are no songs in the queue.", "value": "Please play a song first before skipping.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /skip but there are no songs in the queue.")
        elif index is None:
            ctx.voice_client.stop()
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "skip",
                fields = [
                    {"name": "Skipped", "value": f"The currently playing song has been skipped.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)
        elif index > songQueue.length():
            embed = await embedPackaging.packEmbed(
                title = "Error: Invalid index",
                embedType = "error",
                command = "skip",
                fields = [
                    {"name": "The index you provided is invalid.", "value": "Please make sure you are providing a valid index.\nIf you believe this is an error, please open an issue on [GitHub](https://githubcom/3underscoreN/3_n-s-slash-Music-Bot).","inline":False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /skip but provided an invalid index.")
        else:
            RemovedSong = songQueue.remove(index - 1)
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "skip",
                fields = [
                    {"name": "Skipped", "value": f"The song at index **{index}**: `{RemovedSong[0].title}` has been skipped.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)

    @commands.slash_command(name = "stop", description = "Stops the bot and clears the queue.")
    async def stop(self, ctx):
        global songQueue
        if songQueue.current is None:
            embed = await embedPackaging.packEmbed(
                title = "Error: No songs in queue",
                embedType = "error",
                command = "stop",
                fields = [
                    {"name": "There are no songs in the queue.", "value": "Please play a song first before stopping.\nIf you believe this is an error, please open an issue on [GitHub](https://githubcom/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /stop but there are no songs in the queue.")
        else:
            songQueue.reset()
            ctx.voice_client.stop()
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "stop",
                fields = [
                    {"name": "Stopped", "value": f"The bot has been stopped and the queue has been cleared.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)

    @commands.slash_command(name = "pause", description = "Pauses the currently playing song.")
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            embed = await embedPackaging.packEmbed(
                title = "Error: Already paused",
                embedType = "error",
                command = "pause",
                fields = [
                    {"name": "The bot is already paused.", "value": "Please make sure the bot is not paused before pausing.\nIf you believe this is an error, please open an issue on [GitHub](https://githubcom/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /pause but the bot is already paused.")
        else:
            ctx.voice_client.pause()
            embed = await embedPackaging.packEmbed(
                title = "Success", 
                embedType = "success", 
                command = "pause", 
                fields = [
                    {"name": "Paused", "value": "The currently playing song has been paused.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)

    @commands.slash_command(name = "resume", description = "Resumes the currently paused song.")
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            # embed = discord.Embed(title = "Success", color = 0x00ff00)
            # embed.add_field(name = "Resumed", value = f"The bot has been resumed.", inline = False)
            # embed.set_footer(text = "resume · Bot made by 3_n#7069")
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "resume",
                fields = [
                    {"name": "Resumed", "value": "The bot has been resumed.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)
        else:
            # embed = discord.Embed(title = "Error: Not paused", color = 0xff0000)
            # embed.add_field(name = "The bot is not paused.", value = "Please make sure the bot is paused before resuming.\nIf you believe this is an error, please open an issue on [GitHub](https://githubcom/3underscoreN/3_n-s-slash-Music-Bot)." , inline = False)
            # embed.set_footer(text = "resume · Bot made by 3_n#7069")
            embed = await embedPackaging.packEmbed(
                title = "Error: Not paused",
                embedType = "error",
                command = "resume",
                fields = [
                    {"name": "The bot is not paused.", "value": "Please make sure the bot is paused before resuming.\nIf you believe this is an error, please open an issue on [GitHub](https://githubcom/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            logging.warn(f"{ctx.author} tried to run /resume but the bot is not paused.")

    @commands.slash_command(name = "search", description = "Searches on YouTube and displays the results.")
    @discord.option("query", str, description = "The query to search on YouTube.", required = True)
    async def search(self, ctx, query: str):
        await ctx.defer()
        result = YoutubeSearch(query, max_results = 5).to_dict()
        embeds = []
        for i in range(len(result)):
            this_embed = await embedPackaging.packEmbed(
                    title = f"Search result {i + 1}:",
                    embedType = "info",
                    command = "search",
                    fields = [
                        {"name": "Title", "value": f"[{result[i]['title']}](https://youtube.com{result[i]['url_suffix']})", "inline": False},
                        {"name": "Duration", "value": result[i]["duration"], "inline": False},
                        {"name": "Pro Tip!", "value": f"Click the **green button** to play the song/add the song to queue!\n**NOTE!** The buttons will time out in 60 seconds and it will be unavailable after timeout.", "inline": True}
                    ]
                )
            this_embed.set_thumbnail(url = result[i]["thumbnails"][0])
            embeds.append(this_embed)
        
        paginator = Paginator(embeds, timeout = 60, use_default_buttons = False)
        paginator.add_button(PaginatorButton("first", label = "⏪", style = discord.ButtonStyle.grey))
        paginator.add_button(PaginatorButton("prev", label="◀️", style=discord.ButtonStyle.blurple))
        paginator.add_button(playButton(ctx = ctx, result = result))
        paginator.add_button(PaginatorButton("next", label="▶️", style=discord.ButtonStyle.blurple))
        paginator.add_button(PaginatorButton("last", label="⏩", style=discord.ButtonStyle.grey))
        await paginator.respond(ctx.interaction, ephemeral = True)


        

def setup(bot):
    bot.add_cog(music(bot))

if __name__ == "__main__":
    print("This is not the main script! Run main.py!")