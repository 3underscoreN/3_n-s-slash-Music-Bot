# 3_n's Music Bot (slash command)
 
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

If you do not have the ability to deploy the project, an invitation link is available [here](https://discord.com/api/oauth2/authorize?client_id=984461189704732722&permissions=3147776&scope=bot). However, do keep in mind that support for multiple servers is NOT tested and provided "as is".

## Deploy
Follow the steps to deploy the bot on your server/computer:
1. Clone the repository:
```bash
$ git clone https://github.com/3underscoreN/3_n-s-slash-Music-Bot.git
```
2. Create your own discord bot and fetch your discord token [here](https://discord.com/developers/applications). You also need to obtain your own user ID.

3. Set up these environment variables:
```bash
$ export TOKEN='<your token here>'
$ export OWNER='<your user ID here>'
```

4. Run the bot:
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
If you encountered any undesirable behaviour, please open an issue on this repository.

## Contribution
If you would like to contribute to this project, please open a pull request. I will review it as soon as possible.

## License
This project is licensed under BSD 2-Clause. See the [LICENSE](LICENSE) file for details.