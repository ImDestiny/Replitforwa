import os
from config import Config

class Translation(object):
  START_TXT = """<b>Hey {},{}</b>

◈ I am an Advanced Auto Forward Bot.
◈ I can forward all messages from one channel to another channel.
◈ Click Help button to learn more about me.

<blockquote>Made with ❤️ on Replit</blockquote></b>"""


  HELP_TXT = """<b><u>🛠️ HELP</b></u>

<u>**📚 Available commands:**</u>
<b>⏣ __/start - check I'm alive__ 
⏣ __/forward - forward messages__
⏣ __/tasks - view and resume active tasks__
⏣ __/settings - configure your settings__
⏣ __/reset - reset your settings__</b>

<b><u>💢 Features:</b></u>
<b>► __Forward message from public channel to your channel without admin permission. If the channel is private, admin permission is needed__
► __Forward message from private channel to your channel by using userbot (user must be member in there)__
► __Resume interrupted forwarding tasks__
► __Forward at rate of ~20 messages per minute__
► __Handle Telegram rate limits automatically__
► __Custom caption__
► __Custom button__
► __Support restricted chats__
► __Skip duplicate messages__
► __Filter type of messages__
► __Skip messages based on extensions & keywords & size__</b>
"""
  
  HOW_USE_TXT = """<b><u>⚠️ Before Forwarding:</b></u>
  
<b>► __Add a Bot or Userbot__
► __Add at least one channel (Your Bot/Userbot must be admin in there)__
► __You can add chats or bots by using /settings__
► __If the **From Channel** is private, your userbot must be a member or your bot must have admin permission__
► __Then use /forward to forward messages__
► __If forwarding is interrupted, use /tasks to resume__</b>"""
  
  ABOUT_TXT = """<b>
╭───────────⍟
├◈ My name: <a href='https://t.me/'>Advanced Forwarder Bot</a>
├◈ Library: <a href='https://github.com/pyrogram'>Pyrogram</a>
├◈ Language: <a href='https://www.python.org/'>Python 3</a>
├◈ Database: <a href='https://cloud.mongodb.com/'>MongoDB</a>
├◈ Version: v3.0.0
├◈ Built on Replit
╰───────────────⍟</b>"""
  
  STATUS_TXT = """<b><u>Bot Status</u>

👨 Users: {}

🤖 Bots: {}

📣 Channels: {} 
</b>""" 
  
  FROM_MSG = "<b>❪ SET SOURCE CHAT ❫\n\nForward the last message or last message link of source chat.\n/cancel - cancel this process</b>"
  TO_MSG = "<b>❪ CHOOSE TARGET CHAT ❫\n\nChoose your target chat from the given buttons.\n/cancel - Cancel this process</b>"
  SKIP_MSG = "<b>❪ SET MESSAGE SKIPPING NUMBER ❫</b>\n\n<b>Skip as many messages as the number you enter, and the rest will be forwarded.\nDefault Skip Number =</b> <code>0</code>\n<code>eg: You enter 0 = 0 messages skipped\n You enter 5 = 5 messages skipped</code>\n/cancel <b>- cancel this process</b>"
  CANCEL = "<b>Process Cancelled Successfully!</b>"
  BOT_DETAILS = "<b><u>📄 BOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ BOT ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"
  USER_DETAILS = "<b><u>📄 USERBOT DETAILS</b></u>\n\n<b>➣ NAME:</b> <code>{}</code>\n<b>➣ USER ID:</b> <code>{}</code>\n<b>➣ USERNAME:</b> @{}"  
         
  TEXT = """<b>╭────❰ <u>Forwarded Status</u> ❱────❍
┃
┣⊸<b>🕵 Fetched Msgs:</b> <code>{}</code>
┣⊸<b>✅ Successfully Fwd:</b> <code>{}</code>
┣⊸<b>👥 Duplicate Msgs:</b> <code>{}</code>
┣⊸<b>🗑️ Deleted Msgs:</b> <code>{}</code>
┣⊸<b>🪆 Skipped Msgs:</b> <code>{}</code>
┣⊸<b>📊 Status:</b> <code>{}</code>
┣⊸<b>⏳ Progress:</b> <code>{}</code> %
┣⊸<b>⏰ ETA:</b> <code>{}</code>
┃
╰────⌊ <b>{}</b> ⌉───❍</b>"""
  
  TEXT1 = """
╔════❰ Forward Status ❱➠
║╭━━━━━━━━━━━━━━━➣
║┃
║┣⪼**🕵 Fetched Msgs:** `{}`
║┃
║┣⪼**✅ Successfully Fwd:** `{}`
║┃
║┣⪼**👥 Duplicate Msgs:** `{}`
║┃
║┣⪼**🗑️ Deleted Msgs:** `{}`
║┃
║┣⪼**🪆 Skipped Msgs:** `{}`
║┃
║┣⪼**📊 Status:** `{}`
║┃
║┣⪼**⏳ Progress:** `{}`
║┃
║┣⪼**⏰ ETA:** `{}`
║┃
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ **{}** ❱➠ """
  
  DUPLICATE_TEXT = """
╔════❰ Unequify Status ❱
║╭━━━━━━━━━━━━━━━➣
║┣⪼ <b>Fetched Files:</b> <code>{}</code>
║┃
║┣⪼ <b>Duplicate Deleted:</b> <code>{}</code> 
║╰━━━━━━━━━━━━━━━➣
╚════❰ ❱
"""
  DOUBLE_CHECK = """<b><u>DOUBLE CHECKING ⚠️</b></u>
<code>Before forwarding the messages, click the Yes button only after checking the following:</code>

<b>★ YOUR BOT:</b> [{botname}](t.me/{botuname})
<b>★ FROM CHANNEL:</b> `{from_chat}`
<b>★ TO CHANNEL:</b> `{to_chat}`
<b>★ SKIP MESSAGES:</b> `{skip}`

<i>° [{botname}](t.me/{botuname}) must be admin in **TARGET CHAT**</i> (`{to_chat}`)
<i>° If the **SOURCE CHAT** is private, your userbot must be a member or your bot must be admin there also</b></i>

<b>If the above is checked then the Yes button can be clicked</b>"""

  # New messages for task resume functionality
  TASK_RESUME = "<b>❪ RESUME FORWARDING ❫\n\nYou have a forwarding task that was interrupted. Would you like to resume?\n/cancel - Cancel this process</b>"
  NO_TASKS = "<b>You don't have any active forwarding tasks to resume.</b>"
  TASK_DETAILS = """<b><u>📄 TASK DETAILS</b></u>
<b>➣ TASK ID:</b> <code>{}</code>
<b>➣ FROM CHAT:</b> <code>{}</code>
<b>➣ TO CHAT:</b> <code>{}</code>
<b>➣ PROGRESS:</b> <code>{}/{}</code>
<b>➣ STATUS:</b> <code>{}</code>
<b>➣ CREATED:</b> <code>{}</code>
"""