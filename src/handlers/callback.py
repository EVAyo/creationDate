"""
Handlers for dealing with callbacks
"""
import json, pathlib  # noqa: E401
from aiogram import Bot, types
from process.database import User
from process.function import Function
from process.utility import (
    clean_message, tree_display, escape_dict, time_format
)


REPLIES = json.load(open(pathlib.Path.cwd().joinpath('src/ui/replies.json')))
interpolation = Function()


async def button_lang(query: types.CallbackQuery):
    user, _ = User.get_or_create(
        user_id=query.from_user.id,
        defaults={'language': 'en'}
    )
    bot = Bot.get_current()

    # bad clients can send arbitrary callback data
    if getattr(query, 'data', None) not in REPLIES['LANGS']:
        return

    user.language = query.data
    user.save()

    await query.answer()
    await bot.edit_message_text(
        text=REPLIES['lang_success'][query.data],
        message_id=query.message.message_id,
        chat_id=query.from_user.id
    )


async def query_with_age(query: types.InlineQuery):
    user, _ = User.get_or_create(
        user_id=query.from_user.id,
        defaults={'language': 'en'}
    )

    # only the user object is used, as there is no forwarding in inline query
    clean = clean_message(query)['from']
    date = time_format(
            unix_time=interpolation.func(int(clean['id']))
    )
    clean['registered'] = date

    escaped = escape_dict(clean)
    tree = REPLIES['message'][user.language] + tree_display(escaped)

    await query.answer(
        results=[
            types.InlineQueryResultArticle(
                id='1',  # id no matter, because we only have 1 article
                title=REPLIES['inline_handler_title'][user.language],
                input_message_content=types.InputTextMessageContent(
                    tree, parse_mode='HTML'
                ),
                description=REPLIES['inline_handler_content'][user.language]
            )
        ],
        cache_time=300,
        is_personal=True
    )

    user.requests += 1
    user.save()
