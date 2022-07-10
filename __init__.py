import asyncio
import glob
import importlib.util
import inspect
import logging
import re
import sys
from pathlib import Path
from typing import Awaitable, Callable

import local_config as Config
import pyrogram
from pyrogram import Client

logging.basicConfig(format="%(asctime)s - [ %(name)-33s ] - %(message)s", level=logging.INFO)


class TgUserBot(Client):
    def __init__(self, session_name, api_id, api_hash):
        super().__init__(session_name, api_id, api_hash)

    def log(self, *args, **kwargs):
        frame = inspect.stack()[1]
        func_name = frame.function
        funcobj = frame.frame.f_globals[func_name]
        if hasattr(funcobj, "LOG_NAME"):
            logname = frame.frame.f_globals[func_name].LOG_NAME
            logging.getLogger(logname).info(*args, **kwargs)
        else:
            logging.getLogger(f"{func_name}").info(*args, **kwargs)


UserBot = TgUserBot(Config.BOT_SESSION_NAME, Config.APP_ID, Config.API_HASH)


class Registration:
    def __init__(self,
                 module: str,
                 hookname: str,
                 pattern: str = None,
                 outgoing: bool = None,
                 incoming: bool = None,
                 groupId: int = None,
                 channelId: int = None,
                 edited_only: bool = None,
                 deleted_only: bool = None,
                 callback: Callable = None) -> None:
        self.module = module
        self.hookname = hookname
        self.pattern = pattern
        self.outgoing = outgoing
        self.incoming = incoming
        self.groupId = groupId
        self.channelId = channelId
        self.edited_only = edited_only
        self.deleted_only = deleted_only
        self._callback: Awaitable = callback
        if callback is None:
            raise Exception("No callback defined")
        pass

    def matches(self, event: pyrogram.types.Message, isEdited: bool = False, isDeleted: bool = False) -> bool:
        if self.pattern is not None:
            if event.text is None:
                return False

            if not re.match(self.pattern, event.text):
                return False

        # If not both True nor False
        if not (self.incoming and self.outgoing) and not (not self.incoming and not self.outgoing):
            if self.outgoing is not None:
                # We need outgoing but the event is not.
                if self.outgoing and not event.outgoing:
                    return False
            if self.incoming is not None:
                # We need incoming but the event is outgoing.
                if self.incoming and event.outgoing:
                    return False

        if self.groupId is not None:
            if event.chat is None or self.groupId != event.chat.id:
                return False

        if self.channelId is not None:
            if self.channelId is not event.channel_chat_created:
                return False

        if self.edited_only is None:
            if isEdited:
                return False
        else:
            if self.edited_only != isEdited:
                return False

        if self.deleted_only is None:
            if isDeleted:
                return False
        else:
            if self.deleted_only != isDeleted:
                return False

        if (event.chat is None) or ((not event.outgoing) and event.chat.id not in Config.INCOMING_MESSAGE_ALLOWLIST):
            return False

        return True

    def create_task(self, event: pyrogram.types.Message) -> asyncio.Task:
        return asyncio.create_task(self._callback(UserBot, event))


REGISTRATIONS: list[Registration] = []


def load_plugin(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["plugins."+module_name] = mod
    UserBot.log("loading module: " + module_name)
    spec.loader.exec_module(mod)


def register(name: str, pattern: str = None, outgoing: bool = None, incoming: bool = None, groupId: int = None, channelId: int = None, edited_only: bool = None, deleted_only: bool = None):
    module = Path(inspect.stack()[1].filename).stem.replace(".py", "")
    UserBot.log(f"|-- registering '{name}'")

    def decorator(func):
        r = Registration(module, name, pattern, outgoing, incoming, groupId, channelId, edited_only, deleted_only, func)
        REGISTRATIONS.append(r)
        func.REGISTRATION = r
        func.LOG_NAME = f"plugins.{module}.{name}"
        return func
    return decorator


def LoadPlugins(pathglob):
    files = glob.glob(pathglob)
    for fullpathstr in files:
        fullpath = Path(fullpathstr)
        module_name = fullpath.stem.removesuffix(".py")
        if module_name.startswith("_"):
            continue
        load_plugin(module_name, fullpath)


def StartBot():
    UserBot.log("=============================")
    UserBot.log("|      UserBot Started      |")
    UserBot.log("=============================")

    try:
        UserBot.run()
    except KeyboardInterrupt:
        UserBot.stop()
