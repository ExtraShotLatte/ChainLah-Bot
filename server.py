import logging
import config
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

msgs = {}
chains = {}
logs = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.info(f"Start command received from chat_id: {chat_id}")
    print(update)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Add me to a group + grant admin rights to create chains messages for your group!\n/clhelp to see the commands"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.info(f"Start command received from chat_id: {chat_id}")
    print(update)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Use /clset <chaintopic> to set the chain topic.\nUse /cladd <order> to add a message to current chain.\nUse /cledit <index> <essage> to edit a messsage in the current chain.\nUse /cllist to see the current list in your group!\nUse /clremove <index> to remove a message in the chain.\nUse /cllog to see a list of actions your group has made.\nUse /clend to end the current chain.\nUse /clhelp To see this help message again!"
    )

async def setchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) < 1:
        logging.warning(f"Setchain command received with no topic in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Set chain command received with no chaintopic. Use /clset <chaintopic> to start one.")
        return

    topic = ' '.join(context.args)

    if chat_id in chains:
        logging.info(f"Existing chain in {chat_id} with chain: {chains[chat_id]} already exists!")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Existing chain already exists! Chain: {chains[chat_id]}"
        )
    else:
        chains[chat_id] = topic
        msgs[chat_id] = []
        logs[chat_id] = []
        logging.info(f"Chain set in chat_id {chat_id} with topic: {topic}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Chain started: {topic}"
        )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in chains:
        logging.warning(f"Add command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="No chain set. Use /clset <chaintopic> to start one.")
        return

    user = update.message.from_user.username or update.message.from_user.first_name
    user_chain_message = ' '.join(context.args)

    msgs[chat_id].append(user_chain_message)
    logs[chat_id].append(f"{user} added: {user_chain_message}")
    logging.info(f"Message added by user {user} in chat_id {chat_id}: {user_chain_message}")

    # Delete the user's message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        logging.info(f"Deleted message from user {user} in chat_id {chat_id}")
    except:
        logging.error(f"Failed to delete user message in chat_id {chat_id}: {e}")
        await context.bot.send_message(chat_id, text="Failed to delete previous message, are you sure I am admin?.")

    # Delete the previous chain add message
    if 'chain_message_id' in context.chat_data and context.chat_data['chain_message_id']:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.chat_data['chain_message_id'])
        except Exception as e:
            logging.error(f"Failed to delete previous order list message in chat_id {chat_id}: {e}")
            await context.bot.send_message(chat_id, text="Failed to delete previous message, are you sure I am admin?.")

    # Update the order list message
    message_list = format_message(chains[chat_id], msgs[chat_id])
    msg = await context.bot.send_message(chat_id=chat_id, text=message_list)
    context.chat_data['chain_message_id'] = msg.message_id
    logging.info(f"Created new chain list message in chat_id {chat_id}")

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in chains:
        logging.warning(f"Edit command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="No chain set. Use /clset <chaintopic> to start one.")
        return

    if len(context.args) < 2:
        logging.warning(f"Edit command received with insufficient arguments in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Edit command requires an index and a new order. Use /cledit <index> <new_chain_message>.")
        return

    try:
        index = int(context.args[0]) - 1
        new_chain_message = ' '.join(context.args[1:])

        if 0 <= index < len(msgs[chat_id]):
            old_chain_message = msgs[chat_id][index]
            msgs[chat_id][index] = new_chain_message
            logs[chat_id].append(f"{update.message.from_user.username or update.message.from_user.first_name} edited: {old_chain_message} -> {new_chain_message}")
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            logging.info(f"Deleted message in chat_id {chat_id}")
            logging.info(f"Message at index {index + 1} edited in chat_id {chat_id}: {new_chain_message}")
            await update_message_list_message(chat_id, context)
        else:
            logging.warning(f"Edit command received with invalid index in chat_id: {chat_id}")
            await context.bot.send_message(chat_id, text="Invalid index. Use /cledit <index> <new_chain_message>.")
    except ValueError:
        logging.warning(f"Edit command received with non-integer index in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Index must be an integer. Use /cledit <index> <new_chain_message>.")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in chains:
        logging.warning(f"Remove command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="No chain set. Use /clset <chaintopic> to start one.")
        return

    if len(context.args) < 1 or not context.args[0].isdigit():
        logging.warning(f"Remove command received with invalid index in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Remove command received with invalid index. Use /clremove <index> to remove a message.")
        return

    index = int(context.args[0]) - 1

    if index < 0 or index >= len(msgs[chat_id]):
        logging.warning(f"Remove command received with out-of-range index in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Remove command received with out-of-range index. Use /clremove <index> to remove a message.")
        return

    removed_chain_message = msgs[chat_id].pop(index)
    logs[chat_id].append(f"{update.message.from_user.username or update.message.from_user.first_name} removed: {removed_chain_message}")
    logging.info(f"Message removed in chat_id {chat_id}: {removed_chain_message}")

    # Delete the previous order list message
    if 'chain_message_id' in context.chat_data and context.chat_data['chain_message_id']:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.chat_data['chain_message_id'])
        except Exception as e:
            logging.error(f"Failed to delete previous chain list message in chat_id {chat_id}: {e}")

    # Update the order list message
    message_list = format_message(chains[chat_id], msgs[chat_id])
    msg = await context.bot.send_message(chat_id=chat_id, text=message_list)
    context.chat_data['chain_message_id'] = msg.message_id
    logging.info(f"Created new order list message in chat_id {chat_id}")


async def endchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chains:
        final_message_list = f"Final Chain: {chains[chat_id]}\n" + "\n".join([f"{i + 1} - {o}" for i, o in enumerate(msgs[chat_id])])
        action_log = "\n".join(logs[chat_id])
        await context.bot.send_message(chat_id=chat_id, text=f"Action log:\n{action_log}")
        await context.bot.send_message(chat_id=chat_id, text=f"Chain ended: {chains[chat_id]}")
        await context.bot.send_message(chat_id=chat_id, text=final_message_list)
        logging.info(f"Chain ended in chat_id {chat_id} with topic: {chains[chat_id]}")
        del chains[chat_id]
        del msgs[chat_id]
        del logs[chat_id]
        context.chat_data.pop('chain_message_id', None)
    else:
        logging.warning(f"Endchain command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id=chat_id, text="No active order chain to end.")

async def update_message_list_message(chat_id, context):
    print(msgs[chat_id])
    message_list = f"Chain: {chains[chat_id]}\n" + "\n".join([f"{i + 1} - {o}" for i, o in enumerate(msgs[chat_id])])

    if 'chain_message_id' not in context.chat_data:
        context.chat_data['chain_message_id'] = None

    if context.chat_data['chain_message_id']:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=context.chat_data['chain_message_id'],
                text=message_list
            )
            logging.info(f"Updated order list message in chat_id {chat_id}")
        except Exception as e:
            logging.error(f"Failed to edit message in chat_id {chat_id}: {e}")
            msg = await context.bot.send_message(chat_id=chat_id, text=message_list)
            context.chat_data['chain_message_id'] = msg.message_id
            logging.info(f"Created new order list message in chat_id {chat_id}")
    else:
        msg = await context.bot.send_message(chat_id=chat_id, text=message_list)
        context.chat_data['chain_message_id'] = msg.message_id
        logging.info(f"Created new chain list message in chat_id {chat_id}")

async def list_msgs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chains:
        message_list = f"Chain: {chains[chat_id]}\n" + "\n".join(msgs[chat_id])
        await context.bot.send_message(chat_id=chat_id, text=message_list)
        logging.info(f"List command received in chat_id {chat_id}")
    else:
        logging.warning(f"List command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id=chat_id, text="No active order chain to list.")

# For debugging purpose
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text

    logging.info(f"Message from {user} in chat_id {chat_id}: {message_text}")

    await context.bot.send_message(config.USER_ID, text=f"Message from {user} in chat_id {chat_id}: {message_text}")
    await context.bot.forward_message(config.USER_ID, from_chat_id=chat_id, message_id=update.message.message_id)

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in logs:
        action_log = "\n".join(logs[chat_id])
        await context.bot.send_message(chat_id=chat_id, text=f"Action log:\n{action_log}")
    else:
        await context.bot.send_message(chat_id=chat_id, text="No actions logged yet.")

def format_message(topic, msgs):
    res = f"Chain: {topic}\n"
    index = 1
    for msg in msgs:
        res = res + f"{index} - {msg}\n"
        index = index + 1
    return res

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.token).build()
    
    application.add_handler(CommandHandler('clstart', start))
    application.add_handler(CommandHandler('clhelp', help))
    application.add_handler(CommandHandler('clset', setchain))
    application.add_handler(CommandHandler('cladd', add))
    application.add_handler(CommandHandler('cledit', edit))
    application.add_handler(CommandHandler('clremove', remove))
    application.add_handler(CommandHandler('clend', endchain))
    application.add_handler(CommandHandler('cllog', log))
    application.add_handler(CommandHandler('cllist', list_msgs))

    application.add_handler(MessageHandler(~filters.COMMAND, log_message))

    logging.info("Bot started")
    application.run_polling()
    logging.info("Bot stopped")

 