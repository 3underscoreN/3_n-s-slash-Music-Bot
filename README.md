# 3_n's Music Bot (slash command)

### Content
* [Introduction](#introduction)
* [Dependencies](#dependencies)
* [Deploy](#deploy)
* [Error Handling](#error-handling)
* [Issues](#issues)
* [Contribution](#contribution)
* [License](#license)

## Introduction
This is a Discord bot I write in my free time. Following [my last bot](https://github.com/3underscoreN/3_n-s-Music-Bot), since Discord is adding a fancy "slash command" thingy, I decided to rewrite the bot, as well as using new libraries.

## Dependencies
You would need these python packages before you can run this bot:
* [orjson](https://github.com/ijl/orjson)
* [pafy](https://github.com/mps-youtube/pafy)
* [py-cord](https://github.com/Pycord-Development/pycord)
* [PyNaCl](https://github.com/pyca/pynacl/)
* [youtube-dl](https://github.com/ytdl-org/youtube-dl) (Not recommended since it is pretty out of date, check below for alternatives)
* [youtube_search](https://github.com/joetats/youtube_search)
* [pytube](https://github.com/pytube/pytube)

You would also need ffmpeg installed. 

To install these packages, you can use `pip`:
```bash
$ pip uninstall discord
$ pip install orjson pafy py-cord PyNaCl youtube-dl youtube-search pytube
$ pip install -U "py-cord[voice]"

# Optional for performance
$ pip install -U "py-cord[speed]"
```
### Alternatives
Apart from using outdated `youtube-dl`, you can use pafy's backend:
```bash
$ export PAFY_BACKEND="internal"
```
However, as the backend is not well maintained and not tested, I strongly disrecommend you use it.

Another alternative is to use forks. This project is actually developed with [yt-dlp](https://github.com/yt-dlp/yt-dlp). However for this to work you have to tweak pafy `.py` files:
1. Install `yt-dlp`:
```bash
$ pip install yt-dlp
```
2. Find out where `pafy` is installed:
```python
>>> import pafy
>>> pafy.__file__
```
3. Visit the folder and change `import youtube_dl` into `import yt_dlp as youtube_dl` in all of the `.py` files.

If you encountered any problem with this, feel free to join the [Discord server](https://discord.gg/sRgY26cg23) and ask for help.

## Deploy
Follow the steps to deploy the bot on your server/computer:
1. Clone the repository:
```bash
$ git clone https://github.com/3underscoreN/3_n-s-slash-Music-Bot.git
```
2. Create your own discord bot and fetch your discord token [here](https://discord.com/developers/applications). You also need to obtain your own user ID.

3. Get a YouTube Data v3 API key for playlist parsing (optional, but if you want to use addplaylist, you need this). You can get one [here](https://developers.google.com/youtube/v3/getting-started).

4. Set up these environment variables:
```bash
$ export TOKEN='<your token here>'
$ export OWNER='<your user ID here>'
$ export YT_API_KEY='<your youtube api key here>'
```

5. Run the bot:
```bash
$ python3 main.py
```

## Error Handling
There might be some errors if you are using `youtube-dl` or `yt-dlp` as the backend: 
```
KeyError: 'dislike_count'
```
Since YouTube has deperecated the dislike count, calling dislike_count will result in an error. If you experience this error, open `pafy/backend_youtube_dl.py` and comment out this line (on line 54):
```python
self._dislikes = self._ydl_info['dislike_count']
```

You might also get Opus/FFmpeg related errors: 
```
discord.errors.ClientException: ffmpeg was not found.
```
Please ensure ffmpeg is **installed** and **added to your PATH**. Installation of ffmpeg differs from platform to platform, and you can find the installation guide [here](https://ffmpeg.org/download.html).

## Issues

1. When I try to play music, the bot responds the following:
```
ApplicationCommandInvokeError("Application Command raised an exception: TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'")
```
Answer: This is caused by line 107 of `backend_youtube_dl.py` in `pafy`:
```python
self._rawbitrate = info.get('abr', 0) * 1024
```
To fix this, you can change it to:
```python
    if temp_abr := info.get('abr', 0):
        self._rawbitrate = temp_abr * 1024
    else:
        self._rawbitrate = 0
```
Refer to issue [#5](/../../issues/5) for more details.

If you encountered any undesirable behaviour, please open an issue on this repository.

## Contribution
If you would like to contribute to this project, please open a pull request. I will review it as soon as possible.

## License
This project is licensed under BSD 2-Clause. See the [LICENSE](LICENSE) file for details.
