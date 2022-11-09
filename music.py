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
import random
from pytube import Playlist

OWNER = int(os.getenv("OWNER"))

# regex that matches youtube url with video id
YOUTUBE_REGEX = re.compile(r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.{11})")
# regex that match a youtube playlist url 
YOUTUBE_PLAYLIST_REGEX = re.compile(r"(?:https:\/\/)?(?:www\.)?(?:youtube\.com)\/(?:watch\?v=.{11}&|playlist\?)?list=(?:[A-Za-z0-9_-])+")
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class queue():
    """
    Class of a queue, which contains a list of pafy objects and the requester. Also contains the currently playing song and its requester.

    Attributes
    ----------
    queue : list
        A list of queue with each element being in a list of [`pafyObject`, `requester`]. 
        pafyObject is created with `pafy.new()` while requester is a discord.Member object.
    
    current : list
        Indicates  thre currently playing song.
        A list of [`pafyObject`, `requester`]. 
        pafyObject is created with `pafy.new()` while requester is a discord.Member object.

    forceSkip : bool
        Indicates whether the next song should be force skipped.
        Ignores repeat mode for the next queue.next() call.
        If the queue is exhausted, setting this to True will also reset the repeat mode to off upon the next queue.next() call.

    private _repeatMode : int
        Indicates the repeat mode of the queue.
        Should be accessed through `repeatMode` property.


    Methods
    -------
    add(pafyObject, requester) -> int
        Adds a song to the queue. 
        Returns the length of the queue (which can be used to indicated the position of the song in the queue).

    next() -> Union[list, None]
        Updates the `queue` attributes to remove the first song in the list and set it as the `current` attribute according to the repeat mode.
        If forceSkip is True, the next song will be force skipped.
        Returns the `current` attribute after the update.
        If forceSkip is True and the queue is exhausted, the repeat mode will be reset to off and it will return None.
        Otherwise, an IndexError will be raised.

    remove(index) -> list
        Removes a song from the queue. Returns the removed song.

    reset()
        Resets the queue and the current song.
        This function is destructive. All songs in the queue will be lost.

    length() -> int
        Returns the length of the queue.

    Properties
    ----------
    @repeatMode.getter
    def repeatMode() -> int
        Returns the repeat mode of the queue in string. 
        Possible values are "off", "current", and "all".

    @repeatMode.setter
    def repeatMode(mode) -> None
        Sets the repeat mode of the queue.
        The function accepts a string (of how the class returns repeatMode) or an integer.

    Raises
    ------
    IndexError
        Raised when the queue is empty and the next() function is called. (Only when forceSkip is False)
    """
    def __init__(self):
        self.queue = []
        self.current = None
        self._repeatMode = 0 # 0 = off, 1 = repeat current, 2 = repeat queue
        self.forceSkip = False

    def add(self, pafyObject, requester):
        self.queue.append([pafyObject, requester])
        return len(self.queue)

    def next(self):
        if not self.forceSkip:
            if self._repeatMode == 0:
                if len(self.queue) > 0:
                    self.current = self.queue.pop(0)
                    return self.current
                else:
                    raise IndexError("There are no more songs in the queue.")
            if self._repeatMode == 1:
                return self.current
            if self._repeatMode == 2:
                if len(self.queue) > 0:
                    self.current = self.queue.pop(0)
                    self.queue.append(self.current)
                    return self.current
                else:
                    return self.current
        else:
            if len(self.queue) > 0:
                self.current = self.queue.pop(0)
                self.forceSkip = False
                return self.current
            else:
                self.forceSkip = False
                self._repeatMode = 0
                return None

    def remove(self, index):
        return self.queue.pop(index)

    def shuffle(self):
        random.shuffle(self.queue)

    def reset(self):
        self.queue = []
        self.current = None
        self._repeatMode == 0

    def length(self):
        return len(self.queue)

    @property
    def repeatMode(self):
        return self._repeatMode

    @repeatMode.getter
    def repeatMode(self):
        if self._repeatMode == 0:
            return "off"
        if self._repeatMode == 1:
            return "current"
        if self._repeatMode == 2:
            return "queue"

    @repeatMode.setter
    def repeatMode(self, value):
        if value in ["off", 0, "0", "none", "no"]:
            self._repeatMode = 0
            return
        if value in ["current", 1, "1", "this", "single"]:
            self._repeatMode = 1
            return
        if value in ["queue", 2, "2", "all", "list"]:
            self._repeatMode = 2
            return

    

songQueue = queue()

def playnext(ctx):
    try:
        song = songQueue.next()
        if song != None:
            ctx.voice_client.play(discord.FFmpegOpusAudio(song[0].getbestaudio().url, **FFMPEG_OPTIONS), after=lambda e: playnext(ctx))
        else:
            pass # unable to fetch anything from queue.next()
    except IndexError:
        pass # no more songs to play

class playButton(PaginatorButton):
    """
    Subclass of PaginatorButton that plays a song when clicked. This can ONLY be a "page_indicator" button.

    Attributes
    ----------
    ctx: discord.ApplicationContext
        The context of the command that calls the paginator button.
    result: dict
        The result of the youtube search. Should be created with the YoutubeSearch().to_dict() method.

    Methods
    -------
    async def callback(self, interaction: discord.Interaction)
        This method is a coroutine.
        It will be called when the button is clicked and an ``discord.Interaction`` object is created.
    """
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

class skipConfirmView(discord.ui.View):
    """
    Subclass of discord.ui.View that contains buttons to confirm or cancel a skip when repeat mode is current.

    Attributes
    ----------
    ctx: discord.ApplicationContext
        The context of the command that calls the object.
    **kwargs
        Any other keyword arguments. It will be passed to the discord.ui.View superclass.

    Methods
    -------
    async def on_timeout(self):
        This method is a coroutine.
        It will be automatically called when the view times out. (Part of the discord.ui.View superclass, but overwritten here)
        It edits the message to show that the view timed out, as well as stopping interaction listening, and clear all buttons.
    """
    def __init__(self, ctx:discord.ApplicationContext, **kwargs):
        self.ctx = ctx
        super().__init__(**kwargs)

    @discord.ui.button(label = "Confirm and turn off repeat", style = discord.ButtonStyle.green)
    async def confirm_off_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        global songQueue
        songQueue.repeatMode = "off"
        self.ctx.voice_client.stop()
        self.clear_items()
        embed_ephemeral = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "skip",
            fields = [
                {"name": "Skipped", "value": "Operation completed.", "inline": False}
            ]
        )
        await self.message.edit(embed = embed_ephemeral, view = self)
        self.stop()
        embed_Public = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "skip",
            fields = [
                {"name": "Skipped", "value": "The current song has been skipped.", "inline": False},
                {"name": "Repeat Mode", "value": "Repeat mode has been turned off.", "inline": False},
                {"name": "Requester", "value": f"{self.ctx.author.mention}", "inline": False}
            ]
        )
        await interaction.response.send_message(embed = embed_Public)
    
    @discord.ui.button(label = "Confirm and keep repeat", style = discord.ButtonStyle.red)
    async def comfirm_keep_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        global songQueue
        songQueue.forceSkip = True
        self.ctx.voice_client.stop()
        self.clear_items()
        embed_ephemeral = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "skip",
            fields = [
                {"name": "Skipped", "value": "Operation completed.", "inline": False}
            ]
        )
        await self.message.edit(embed = embed_ephemeral, view = self)
        self.stop()
        embed_Public = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "skip",
            fields = [
                {"name": "Skipped", "value": "The current song has been skipped.", "inline": False},
                {"name": "Repeat Mode", "value": "Repeat mode has NOT changed.", "inline": False},
                {"name": "Requester", "value": f"{self.ctx.author.mention}", "inline": False}
            ]
        )
        await interaction.response.send_message(embed = embed_Public)
    
    @discord.ui.button(label = "Cancel", style = discord.ButtonStyle.grey)
    async def cancel_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.clear_items()
        await interaction.response.defer()
        embed = await embedPackaging.packEmbed(
            title = "Cancelled",
            color = 0xffff00,
            command = "skip",
            fields = [
                {"name": "Cancelled", "value": "Operation cancelled. Nothing has been changed.", "inline": False},
            ]
        )
        await self.message.edit(embed = embed, view = self)
        self.stop()

    async def on_timeout(self):
        self.clear_items()
        embed = await embedPackaging.packEmbed(
            title = "Operation cancelled",
            color = 0xffff00,
            command = "skip",
            fields = [
                {"name": "Timed out", "value": "You took too long to respond. The skip has been cancelled.", "inline": False}
            ]
        )
        await self.message.edit(embed = embed, view = self)

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
        

        # join the voice channel if the bot is not in any voice channel
        if ctx.voice_client is None:
            if ctx.author.voice is None:
                embed = await embedPackaging.packEmbed(
                    title = "Error: Not in voice channel",
                    embedType = "error",
                    command = "play",
                    fields = [
                        {"name": "You are not in a voice channel.", "value": "Please join a voice channel and try again.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed, ephemeral = True)
                logging.warn(f"{ctx.author} tried to run /play but was not in any voice channel.")
                return
            else:
                await ctx.author.voice.channel.connect()

        await ctx.defer()

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
            embeds = []
            total_queue_length = sum([songQueue.queue[i][0].length for i in range(songQueue.length())])
            for i in range(0, songQueue.length() // 5 + 1):
                embed = await embedPackaging.packEmbed(
                    title = "Queue",
                    description = f"Repeat mode: `{songQueue.repeatMode}`\nShuffle mode: `{'on' if songQueue.shuffle else 'off'}`",
                    embedType = "info",
                    command = "queue",
                    fields = [
                        {"name": "Now playing", "value": f"[{songQueue.current[0].title}](https://youtube.com/watch?v={songQueue.current[0].videoid})\nDuration: {songQueue.current[0].duration}\nRequested by {songQueue.current[1].mention}", "inline":False}
                    ]
                )
                for j in range((5 * i + 1), (5 * i + 6)):
                    if j > songQueue.length():
                        break
                    embed.add_field( # packEmbed returns a discord.Embed() object, so we can use the add_field() method!
                        name = f"**{j}**", 
                        value = f"[{songQueue.queue[i][0].title}](https://youtube.com/watch?v={songQueue.queue[i][0].videoid})\nDuration: {songQueue.queue[i][0].duration}\nRequested by: {songQueue.queue[i][1].mention}", 
                        inline = False
                    )
                    embed.set_footer(text = f"queue · Total queue length: {str(datetime.timedelta(seconds = total_queue_length))} · Bot made by 3_n#7069 ") # Overwrites the default footer
                embeds.append(embed)
            paginator = Paginator(embeds, timeout = 60)
            await paginator.respond(ctx.interaction)
    
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
            if songQueue.repeatMode != "current":
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
            else:
                confirmMessage = skipConfirmView(ctx, timeout = 60)
                embed = await embedPackaging.packEmbed(
                    title = "Are you sure?",
                    color = 0xffff00,
                    command = "skip",
                    fields = [
                        {"name": "Are you sure you want to skip the current song?", "value": "You are on `current` repeat mode right now.\nConfirm your choices and choose an approiate behavior for repeating songs.", "inline": False},
                        {"name": "Note", "value": "These bottons wll not work after 60 seconds.", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed, view = confirmMessage, ephemeral = True)
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
    @discord.option("items_to_display", description = "The number of items to display.", required = False, default = 5, min_value = 1, max_value = 20)
    async def search(self, ctx, query: str, items_to_display:int):
        await ctx.defer()
        result = YoutubeSearch(query, max_results = items_to_display).to_dict()
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

    @commands.slash_command(name = "repeat", description = "Checks the current repeat mode, or set repeat mode to the passed argument.")
    @discord.option("mode", description = "The mode to set repeat to.", required = False, choices = ["off", "current", "queue"])
    async def repeat(self, ctx, mode:str):
        if mode == None:
            embed = await embedPackaging.packEmbed(
                title = "Repeat mode",
                embedType = "info",
                command = "repeat",
                fields = [
                    {"name": "Current repeat mode", "value": f"The current repeat mode is `{songQueue.repeatMode}`.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)
        else:
            songQueue.repeatMode = mode
            embed = await embedPackaging.packEmbed(
                title = "Success",
                embedType = "success",
                command = "repeat",
                fields = [
                    {"name": "Repeat mode set", "value": f"The repeat mode has been set to `{songQueue.repeatMode}`.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed)

    @commands.slash_command(name = "shuffle", description = "Shuffles the queue.")
    async def shuffle(self, ctx):
        songQueue.shuffle()
        embed = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "shuffle",
            fields = [
                {"name": "The playlist has been shuffled.", "value": f"Use `/queue` to take a look at the shuffled queue.", "inline": False}
            ]
        )
        await ctx.respond(embed = embed)

    @commands.slash_command(name = "addplaylist", description = "Add a playlist to the queue. **Please leave the list small.**")
    @discord.option("url", description = "The playlist URL.", required = True)
    @discord.option("start", description = "The index of the song to start from.", required = False, default = 0, min_value = 1)
    @discord.option("end", description = "The index of the song to end at.", required = False, default = 0, min_value = 1)
    async def addplaylist(self, ctx, url:str, start:int, end:int):
        
        url = YOUTUBE_PLAYLIST_REGEX.match(url)
        if url:
            url = url.group(0)
        else:
            embed = await embedPackaging.packEmbed(
                title = "Error: Invalid URL",
                embedType = "error",
                command = "addplaylist",
                fields = [
                    {"name": "Invalid URL", "value": "Please make sure the URL is a valid YouTube playlist URL.", "inline": False}
                ]
            )
            await ctx.respond(embed = embed, ephemeral = True)
            return

        if ctx.voice_client is None:
            if ctx.author.voice is None:
                embed = await embedPackaging.packEmbed(
                    title = "Error: Not in voice channel",
                    embedType = "error",
                    command = "addplaylist",
                    fields = [
                        {"name": "You are not in a voice channel.", "value": "Please join a voice channel and try again.\nIf you believe this is an error, please open an issue on [GitHub](https://github.com/3underscoreN/3_n-s-slash-Music-Bot).", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed, ephemeral = True)
                logging.warn(f"{ctx.author} tried to run /addplaylist but was not in any voice channel while the bot is not connected to any vcs.")
                return
            else:
                await ctx.author.voice.channel.connect()
        
        if start > end:
            if end != 0:
                embed = await embedPackaging.packEmbed(
                    title = "Error: Invalid range",
                    embedType = "error",
                    command = "addplaylist",
                    fields = [
                        {"name": "Invalid range", "value": "The start index cannot be greater than the end index.", "inline": False}
                    ]
                )
                await ctx.respond(embed = embed, ephemeral = True)
                return
        
        p = Playlist(url)
        await ctx.defer()
        errorCount = 0
        successCount = 0
        if end == 0:
            end = len(p.video_urls)

        for index, videourl in enumerate(p.video_urls[start: min(end, len(p.video_urls))]):
            try:
                item = pafy.new(videourl)
                if index == 0 and (not ctx.voice_client.is_playing()):
                    songQueue.current = [item, ctx.author]
                    source = discord.FFmpegOpusAudio(item.getbestaudio().url, **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source, after = lambda e: playnext(ctx))
                else:
                    songQueue.add(item, ctx.author)
                successCount += 1
            except Exception as e:
                errorCount += 1
                logging.error(f"Error while adding {videourl} to queue: {repr(e)}")
                continue

        embed = await embedPackaging.packEmbed(
            title = "Success",
            embedType = "success",
            command = "addplaylist",
            fields = [
                {"name": "Added to queue", "value": f"Number of songs added: `{successCount}`\nNumber of songs failed to add: `{errorCount}`", "inline": False}
            ]
        )
        await ctx.respond(embed = embed)

def setup(bot):
    bot.add_cog(music(bot))

if __name__ == "__main__":
    print("This is not the main script! Run main.py!")