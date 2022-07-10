# My Telegram Userbot Framework

It's actually a wrapper around [Pyrogram](https://pyrogram.readthedocs.io/en/latest/).

## Usage

1. Define your `local_config.py` file (copy paste from `local_config.sample.py` and edit accordingly).

2. In the main file of your userbot, add the following line:

   ```python
   from userbot import StartBot, LoadPlugins

   pathglob = "plugins/*.py"
   LoadPlugins(pathglob)
   StartBot()
   ```

3. For a simple plugin, you can just add the following line:

   ```python
   from asyncio import sleep
   from random import random
   import pyrogram
   from userbot import TgUserBot, register

   @register("?", pattern="^[？?¿]+$", incoming=True)
   async def _(bot: TgUserBot, message: pyrogram.types.Message):
       if random() < 0.7:
           await sleep(random() * 4)
           await message.reply_text("？", quote=True)

   ```

## License

GPLv3
