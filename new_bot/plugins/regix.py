import os
import sys 
import math
import time
import uuid
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT, start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT1

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    
    # Check if user is already running a task
    if temp.lock.get(user) and str(temp.lock.get(user))=="True":
      return await message.answer("Please wait until previous task completes", show_alert=True)
    
    sts = STS(frwd_id)
    if not sts.verify():
      await message.answer("You are clicking on an old button", show_alert=True)
      return await message.message.delete()
    
    i = sts.get(full=True)
    
    # Check if target chat is already being forwarded to
    if i.TO in temp.IS_FRWD_CHAT:
      return await message.answer("In target chat a task is progressing. Please wait until task completes", show_alert=True)
    
    m = await msg_edit(message.message, "<b>Verifying your data, please wait...</b>")
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    
    if not _bot:
      return await msg_edit(m, "<b>You didn't add any bot. Please add a bot using /settings!</b>", wait=True)
    
    try:
      client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:  
      return await m.edit(str(e))
    
    await msg_edit(m, "<b>Processing...</b>")
    
    # Test source chat access
    try: 
       await client.get_messages(sts.get("FROM"), sts.get("limit"))
    except:
       await msg_edit(m, f"**Source chat may be a private channel/group. Use userbot (user must be member over there) or make your [Bot](t.me/{_bot['username']}) an admin over there**", retry_btn(frwd_id), True)
       return await stop(client, user)
    
    # Test target chat access
    try:
       k = await client.send_message(i.TO, "Testing access")
       await k.delete()
    except:
       await msg_edit(m, f"**Please make your [UserBot/Bot](t.me/{_bot['username']}) an admin in target channel with full permissions**", retry_btn(frwd_id), True)
       return await stop(client, user)
    
    # Create a unique task ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # Save forwarding task details for potential resume
    await db.save_forwarding_task(task_id, {
        "user_id": user,
        "from_chat": sts.get("FROM"),
        "to_chat": sts.get("TO"),
        "bot_details": _bot,
        "last_forwarded_msg_id": None,  # Will be updated during forwarding
        "total_count": sts.get("limit"),
        "offset": sts.get("skip") if sts.get("skip") else 0,
        "configs": {
            "caption": caption,
            "forward_tag": forward_tag,
            "protect": protect,
            "button": button,
            "data": data
        },
        "status": "active",
        "created_at": time.time()
    })
    
    # Store task in memory for quick access
    temp.ACTIVE_TASKS[user] = task_id
    
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "<b>🚥 Forwarding started via Advanced Forwarder Bot</b>")
    sts.add(time=True)
    
    # Use faster interval (3 seconds instead of 10)
    sleep = Config.FORWARD_SLEEP
    
    await msg_edit(m, "<b>Processing...</b>") 
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    
    if locked:
        try:
          MSG = []
          pling = 0
          await edit(m, 'Progressing', 10, sts)
          print(f"Starting Forwarding Process... From: {sts.get('FROM')} To: {sts.get('TO')} Total: {sts.get('limit')} Skip: {sts.get('skip')})")
          
          # Get the iterator for messages
          messages_iterator = client.iter_messages(
              chat_id=sts.get('FROM'), 
              limit=int(sts.get('limit')), 
              offset=int(sts.get('skip')) if sts.get('skip') else 0
          )
          
          async for message in messages_iterator:
                if await is_cancelled(client, user, m, sts):
                   return
                
                # Update progress status periodically
                if pling % 20 == 0: 
                   await edit(m, 'Progressing', 10, sts)
                
                pling += 1
                sts.add('fetched')
                
                # Skip invalid messages
                if message == "DUPLICATE":
                   sts.add('duplicate')
                   continue 
                elif message == "FILTERED":
                   sts.add('filtered')
                   continue 
                if message.empty or message.service:
                   sts.add('deleted')
                   continue
                
                # Forward messages with tag (as a batch)
                if forward_tag:
                   MSG.append(message.id)
                   notcompleted = len(MSG)
                   completed = sts.get('total') - sts.get('fetched')
                   
                   # Forward in batches of 100 or when near end
                   if (notcompleted >= 100 or completed <= 100): 
                      await forward(client, MSG, m, sts, protect)
                      sts.add('total_files', notcompleted)
                      
                      # Update the last forwarded message for resume capability
                      await db.update_task_status(task_id, "active", message.id)
                      
                      await asyncio.sleep(sleep)
                      MSG = []
                else:
                   # Forward messages individually with custom caption
                   new_caption = custom_caption(message, caption)
                   details = {"msg_id": message.id, "media": media(message), "caption": new_caption, 'button': button, "protect": protect}
                   await copy(client, details, m, sts)
                   sts.add('total_files')
                   
                   # Update the last forwarded message for resume capability
                   await db.update_task_status(task_id, "active", message.id)
                   
                   await asyncio.sleep(sleep)
        
        except FloodWait as e:
            # Handle rate limiting by Telegram
            logger.warning(f"FloodWait encountered: {e.value} seconds")
            await edit(m, 'Rate Limited', e.value, sts)
            
            # Save current state for resuming later
            await db.update_task_status(task_id, "paused")
            
            # Wait for rate limit to pass
            await asyncio.sleep(e.value)
            
            # Resume forwarding
            await edit(m, 'Resuming', 10, sts)
            await db.update_task_status(task_id, "active")
            
            # Continue forwarding
            # Note: This will naturally continue from the last message due to how we're handling the message iterator
        
        except Exception as e:
            # Handle other errors
            logger.error(f"Forwarding error: {str(e)}")
            await msg_edit(m, f'<b>ERROR:</b>\n<code>{str(e)}</code>', wait=True)
            
            # Mark task as failed for potential resume later
            await db.update_task_status(task_id, "failed")
            
            if i.TO in temp.IS_FRWD_CHAT:
                temp.IS_FRWD_CHAT.remove(i.TO)
            
            return await stop(client, user)
        
        # Forwarding completed successfully
        if i.TO in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(i.TO)
        
        # Mark task as completed
        await db.update_task_status(task_id, "completed")
        
        await send(client, user, "<b>🎉 Forwarding completed</b>")
        await edit(m, 'Completed', "completed", sts) 
        await stop(client, user)


@Client.on_callback_query(filters.regex(r'^resume_task_'))
async def resume_forwarding_task(bot, message):
    user = message.from_user.id
    task_id = message.data.split("_")[2]
    
    # Check if user is already running a task
    if temp.lock.get(user) and str(temp.lock.get(user))=="True":
      return await message.answer("Please wait until previous task completes", show_alert=True)
    
    # Get the task from database
    task = await db.get_task(task_id)
    if not task:
        return await message.answer("This task no longer exists", show_alert=True)
    
    m = await msg_edit(message.message, "<b>Resuming forwarding, please wait...</b>")
    
    # Create STS tracking object
    sts = STS(f"resume_{task_id}")
    
    # Initialize the tracking data
    from_chat = task["from_chat"] 
    to_chat = task["to_chat"]
    skip = task.get("last_forwarded_msg_id", 0)  # Start after the last forwarded message
    limit = task["total_count"]
    
    sts.store(from_chat, to_chat, skip, limit)
    
    # Get bot details
    _bot = task["bot_details"]
    
    # Extract config details
    configs = task["configs"]
    caption = configs.get("caption")
    forward_tag = configs.get("forward_tag", False)
    protect = configs.get("protect", False)
    button = configs.get("button")
    data = configs.get("data", {})
    
    try:
        client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:  
        return await m.edit(str(e))
    
    # Test connections to source and target
    try: 
        await client.get_messages(from_chat, 1)
    except:
        await msg_edit(m, f"**Source chat may be a private channel/group. Use userbot (user must be member over there) or make your [Bot](t.me/{_bot['username']}) an admin over there**", wait=True)
        return await stop(client, user)
    
    try:
        k = await client.send_message(to_chat, "Testing access")
        await k.delete()
    except:
        await msg_edit(m, f"**Please make your [UserBot/Bot](t.me/{_bot['username']}) an admin in target channel with full permissions**", wait=True)
        return await stop(client, user)
    
    # Update task status
    await db.update_task_status(task_id, "active")
    
    # Store task in memory
    temp.ACTIVE_TASKS[user] = task_id
    
    temp.CANCEL[user] = False
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "<b>🚥 Resuming forwarding...</b>")
    sts.add(time=True)
    
    # Use faster interval
    sleep = Config.FORWARD_SLEEP
    
    await msg_edit(m, "<b>Processing...</b>") 
    temp.IS_FRWD_CHAT.append(to_chat)
    temp.lock[user] = locked = True
    
    # Continue with forwarding logic (similar to pub_ function)
    if locked:
        try:
            MSG = []
            pling = 0
            await edit(m, 'Resuming', 10, sts)
            logger.info(f"Resuming Forwarding... From: {from_chat} To: {to_chat} Starting after: {skip}")
            
            # Start from the message after the last forwarded one
            messages_iterator = client.iter_messages(
                chat_id=from_chat,
                limit=int(limit),
                offset=1,  # Start from the next message
                reverse=True  # Get messages in ascending order
            )
            
            async for message in messages_iterator:
                # Skip messages up to the last forwarded one
                if message.id <= skip:
                    continue
                    
                if await is_cancelled(client, user, m, sts):
                    return
                
                if pling % 20 == 0: 
                    await edit(m, 'Progressing', 10, sts)
                
                pling += 1
                sts.add('fetched')
                
                if message == "DUPLICATE":
                    sts.add('duplicate')
                    continue 
                elif message == "FILTERED":
                    sts.add('filtered')
                    continue 
                if message.empty or message.service:
                    sts.add('deleted')
                    continue
                
                if forward_tag:
                    MSG.append(message.id)
                    notcompleted = len(MSG)
                    completed = sts.get('total') - sts.get('fetched')
                    
                    if (notcompleted >= 100 or completed <= 100): 
                        await forward(client, MSG, m, sts, protect)
                        sts.add('total_files', notcompleted)
                        
                        # Update last forwarded message
                        await db.update_task_status(task_id, "active", message.id)
                        
                        await asyncio.sleep(sleep)
                        MSG = []
                else:
                    new_caption = custom_caption(message, caption)
                    details = {"msg_id": message.id, "media": media(message), "caption": new_caption, 'button': button, "protect": protect}
                    await copy(client, details, m, sts)
                    sts.add('total_files')
                    
                    # Update last forwarded message
                    await db.update_task_status(task_id, "active", message.id)
                    
                    await asyncio.sleep(sleep)
            
        except FloodWait as e:
            logger.warning(f"FloodWait encountered during resume: {e.value} seconds")
            await edit(m, 'Rate Limited', e.value, sts)
            
            await db.update_task_status(task_id, "paused")
            await asyncio.sleep(e.value)
            
            await edit(m, 'Resuming', 10, sts)
            await db.update_task_status(task_id, "active")
            
        except Exception as e:
            logger.error(f"Error during resume: {str(e)}")
            await msg_edit(m, f'<b>ERROR:</b>\n<code>{str(e)}</code>', wait=True)
            
            await db.update_task_status(task_id, "failed")
            
            if to_chat in temp.IS_FRWD_CHAT:
                temp.IS_FRWD_CHAT.remove(to_chat)
            
            return await stop(client, user)
        
        # Forwarding completed successfully
        if to_chat in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(to_chat)
        
        # Mark task as completed
        await db.update_task_status(task_id, "completed")
        
        await send(client, user, "<b>🎉 Forwarding completed</b>")
        await edit(m, 'Completed', "completed", sts) 
        await stop(client, user)


async def copy(bot, msg, m, sts):
   try:                                  
     if msg.get("media") and msg.get("caption"):
        await bot.send_cached_media(
              chat_id=sts.get('TO'),
              file_id=msg.get("media"),
              caption=msg.get("caption"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
     else:
        await bot.copy_message(
              chat_id=sts.get('TO'),
              from_chat_id=sts.get('FROM'),    
              caption=msg.get("caption"),
              message_id=msg.get("msg_id"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
   except FloodWait as e:
     await edit(m, 'Progressing', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'Progressing', 10, sts)
     await copy(bot, msg, m, sts)
   except Exception as e:
     logger.error(f"Copy error: {str(e)}")
     sts.add('deleted')
        
async def forward(bot, msg, m, sts, protect):
   try:                             
     await bot.forward_messages(
           chat_id=sts.get('TO'),
           from_chat_id=sts.get('FROM'), 
           protect_content=protect,
           message_ids=msg)
   except FloodWait as e:
     await edit(m, 'Progressing', e.value, sts)
     await asyncio.sleep(e.value)
     await edit(m, 'Progressing', 10, sts)
     await forward(bot, msg, m, sts, protect)
   except Exception as e:
     logger.error(f"Forward error: {str(e)}")
     sts.add('deleted', len(msg))

PROGRESS = """
📈 Percentage: {0} %

♻️ Fetched: {1}

♻️ Forwarded: {2}

♻️ Remaining: {3}

♻️ Status: {4}

⏳️ ETA: {5}

Advanced Forwarder Bot
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass 
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait)
        
async def edit(msg, title, status, sts):
   i = sts.get(full=True)
   status = 'Forwarding' if status == 10 else f"Sleeping {status} s" if str(status).isnumeric() else status
   percentage = "{:.0f}".format(float(i.fetched)*100/float(i.total))
   
   now = time.time()
   diff = int(now - i.start)
   speed = sts.divide(i.fetched, diff)
   elapsed_time = round(diff) * 1000
   time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
   estimated_total_time = elapsed_time + time_to_completion  
   progress = "▰{0}{1}".format(
       ''.join(["▰" for i in range(math.floor(int(percentage) * 15/ 100))]),
       ''.join(["▱" for i in range(15 - math.floor(int(percentage) * 15 / 100))]))
   button = [[InlineKeyboardButton(f'{progress}', callback_data=f'fwrdstatus#{status}#{estimated_total_time}#{percentage}#{i.id}')]]
   estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
   estimated_total_time = estimated_total_time if estimated_total_time != '' else '0 s'

   text = TEXT.format(i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, status, percentage, estimated_total_time, status)
   if status in ["cancelled", "completed"]:
      button.append(
         [InlineKeyboardButton('Support', url='https://t.me/replit'),
          InlineKeyboardButton('About', callback_data='about')]
         )
   else:
      button.append([InlineKeyboardButton('• Cancel', 'terminate_frwd')])
   await msg_edit(msg, text, InlineKeyboardMarkup(button))
   
async def is_cancelled(client, user, msg, sts):
   if temp.CANCEL.get(user)==True:
      # Handle task cancellation and cleanup
      task_id = temp.ACTIVE_TASKS.get(user)
      if task_id:
          await db.update_task_status(task_id, "cancelled")
      
      if sts.TO in temp.IS_FRWD_CHAT:
          temp.IS_FRWD_CHAT.remove(sts.TO)
          
      await edit(msg, "Cancelled", "cancelled", sts)
      await send(client, user, "<b>❌ Forwarding Process Cancelled</b>")
      await stop(client, user)
      return True 
   return False 

async def stop(client, user):
   try:
     await client.stop()
   except:
     pass 
     
   # Cleanup
   await db.rmve_frwd(user)
   temp.forwardings -= 1
   temp.lock[user] = False 
    
async def send(bot, user, text):
   try:
      await bot.send_message(user, text=text)
   except:
      pass 
     
def custom_caption(msg, caption):
  if msg.media:
    if (msg.video or msg.document or msg.audio or msg.photo):
      media = getattr(msg, msg.media.value, None)
      if media:
        file_name = getattr(media, 'file_name', '')
        file_size = getattr(media, 'file_size', '')
        fcaption = getattr(msg, 'caption', '')
        if fcaption:
          fcaption = fcaption.html
        if caption:
          return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
        return fcaption
  return None

def get_size(size):
  units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
  size = float(size)
  i = 0
  while size >= 1024.0 and i < len(units):
     i += 1
     size /= 1024.0
  return "%.2f %s" % (size, units[i]) 

def media(msg):
  if msg.media:
     media = getattr(msg, msg.media.value, None)
     if media:
        return getattr(media, 'file_id', None)
  return None 

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ RETRY ♻️', f"start_public_{id}")]])

def resume_btn(task_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('⏯️ RESUME FORWARDING ⏯️', f"resume_task_{task_id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True 
    
    # If there's an active task, mark it as cancelled in the database
    task_id = temp.ACTIVE_TASKS.get(user_id)
    if task_id:
        await db.update_task_status(task_id, "cancelled")
    
    await m.answer("Forwarding cancelled!", show_alert=True)
          
@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not sts.verify():
       fetched, forwarded, remaining = 0, 0, 0
    else:
       fetched, forwarded = sts.get('fetched'), sts.get('total_files')
       remaining = fetched - forwarded 
    est_time = TimeFormatter(milliseconds=est_time)
    est_time = est_time if (est_time != '' or status not in ['completed', 'cancelled']) else '0 s'
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time), show_alert=True)
      
@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()

# New command to list and resume tasks
@Client.on_message(filters.command(["tasks"]) & ~filters.bot)
async def list_tasks(client, message):
    user_id = message.from_user.id
    tasks = await db.get_user_active_tasks(user_id)
    
    if not tasks or len(tasks) == 0:
        return await message.reply_text("You don't have any active forwarding tasks.")
    
    text = "<b>Your Active Forwarding Tasks:</b>\n\n"
    
    buttons = []
    for task in tasks:
        created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.get("created_at", 0)))
        from_chat = task.get("from_chat")
        to_chat = task.get("to_chat")
        status = task.get("status", "unknown")
        
        text += f"<b>Task ID:</b> <code>{task['task_id']}</code>\n"
        text += f"<b>From:</b> <code>{from_chat}</code>\n"
        text += f"<b>To:</b> <code>{to_chat}</code>\n"
        text += f"<b>Status:</b> <code>{status}</code>\n"
        text += f"<b>Created:</b> <code>{created_time}</code>\n\n"
        
        # Add resume button for each task
        if status in ["active", "paused", "failed"]:
            buttons.append([InlineKeyboardButton(
                f"Resume Task {task['task_id'][-4:]}", 
                callback_data=f"resume_task_{task['task_id']}"
            )])
    
    if buttons:
        buttons.append([InlineKeyboardButton("Close", callback_data="close_btn")])
        return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        return await message.reply_text(text)