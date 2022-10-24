# 3_n's Music Bot (slash command only)
 
## Introduction
This is a Discord bot I write in my free time. Following [my last bot](https://github.com/3underscoreN/3_n-s-Music-Bot), since Discord is adding a fancy "slash command", I decided to rewrite the bot, as well as using new libraries.

## Dependencies
You would need these python packages before you can run this bot:
* [orjson](https://github.com/ijl/orjson)
* [pafy](https://github.com/mps-youtube/pafy)
* [py-cord](https://github.com/Pycord-Development/pycord)
* [PyNaCl](https://github.com/pyca/pynacl/)
* [youtube-dl](https://github.com/ytdl-org/youtube-dl) (Not recommended since it is pretty out of date, check below for alternatives)
* [youtube_search](https://github.com/joetats/youtube_search)

To install these packages, you can use `pip`:
```bash
$ pip uninstall discord
$ pip install orjson pafy py-cord PyNaCl youtube-dl youtube-search
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
