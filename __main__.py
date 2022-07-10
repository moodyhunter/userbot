import asyncio

import pyrogram

from userbot import REGISTRATIONS, StartBot, UserBot, load_plugin


async def process_message(message, **kwargs):
    futures = [r.create_task(message) for r in REGISTRATIONS if r.matches(message, **kwargs)]
    if futures:
        await asyncio.wait(futures)


@UserBot.on_message(filters=pyrogram.filters.all)
async def new_message_handler_impl(_, message: pyrogram.types.Message):
    await process_message(message)


@UserBot.on_deleted_messages(filters=pyrogram.filters.all)
async def deleted_message_handler_impl(_, message: pyrogram.types.Message):
    for m in message:
        await process_message(m, isDeleted=True)


@UserBot.on_edited_message(filters=pyrogram.filters.all)
async def edited_message_handler_impl(_, message: pyrogram.types.list.List):
    await process_message(message, isEdited=True)

if __name__ == "__main__":
    StartBot()
    print("Bot Stopped!")
    exit(0)
