import logging
import config
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

orders = {}
chains = {}
logs = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.info(f"Start command received from chat_id: {chat_id}")
    print(update)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Use /setchain <chaintopic> to set the chain topic.\nUse /add <order> to add your order.\nUse /edit <index> <new_order> to edit an order.\nUse /remove <index> to remove an order.\nUse /endchain to end the current chain."
    )

async def setchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if len(context.args) < 1:
        logging.warning(f"Setchain command received with no topic in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Set chain command received with no chaintopic. Use /setchain <chaintopic> to start one.")
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
        orders[chat_id] = []
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
        await context.bot.send_message(chat_id, text="No chain set. Use /setchain <chaintopic> to start one.")
        return

    user = update.message.from_user.username or update.message.from_user.first_name
    order_text = ' '.join(context.args)

    orders[chat_id].append(f"{len(orders[chat_id]) + 1}. {order_text}")
    logs[chat_id].append(f"{user} added: {order_text}")
    logging.info(f"Order added by user {user} in chat_id {chat_id}: {order_text}")

    # Delete the user's message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        logging.info(f"Deleted message from user {user} in chat_id {chat_id}")
    except:
        logging.error(f"Failed to delete user message in chat_id {chat_id}: {e}")
        await context.bot.send_message(chat_id, text="Failed to delete previous message, are you sure I am admin?.")

    # Delete the previous order list message
    if 'order_message_id' in context.chat_data and context.chat_data['order_message_id']:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.chat_data['order_message_id'])
        except Exception as e:
            logging.error(f"Failed to delete previous order list message in chat_id {chat_id}: {e}")
            await context.bot.send_message(chat_id, text="Failed to delete previous message, are you sure I am admin?.")

    # Update the order list message
    order_list = f"Order Chain: {chains[chat_id]}\n" + "\n".join(orders[chat_id])
    msg = await context.bot.send_message(chat_id=chat_id, text=order_list)
    context.chat_data['order_message_id'] = msg.message_id
    logging.info(f"Created new order list message in chat_id {chat_id}")

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in chains:
        logging.warning(f"Edit command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="No chain set. Use /setchain <chaintopic> to start one.")
        return

    if len(context.args) < 2:
        logging.warning(f"Edit command received with insufficient arguments in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Edit command requires an index and a new order. Use /edit <index> <new_order>.")
        return

    try:
        index = int(context.args[0]) - 1
        new_order = ' '.join(context.args[1:])

        if 0 <= index < len(orders[chat_id]):
            old_order = orders[chat_id][index]
            orders[chat_id][index] = new_order
            logs[chat_id].append(f"{update.message.from_user.username or update.message.from_user.first_name} edited: {old_order} -> {new_order}")
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            logging.info(f"Deleted message in chat_id {chat_id}")
            logging.info(f"Order at index {index + 1} edited in chat_id {chat_id}: {new_order}")
            await update_order_list_message(chat_id, context)
        else:
            logging.warning(f"Edit command received with invalid index in chat_id: {chat_id}")
            await context.bot.send_message(chat_id, text="Invalid index. Use /edit <index> <new_order>.")
    except ValueError:
        logging.warning(f"Edit command received with non-integer index in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Index must be an integer. Use /edit <index> <new_order>.")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in chains:
        logging.warning(f"Remove command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="No chain set. Use /setchain <chaintopic> to start one.")
        return

    if len(context.args) < 1 or not context.args[0].isdigit():
        logging.warning(f"Remove command received with invalid index in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Remove command received with invalid index. Use /remove <index> to remove an order.")
        return

    index = int(context.args[0]) - 1

    if index < 0 or index >= len(orders[chat_id]):
        logging.warning(f"Remove command received with out-of-range index in chat_id: {chat_id}")
        await context.bot.send_message(chat_id, text="Remove command received with out-of-range index. Use /remove <index> to remove an order.")
        return

    removed_order = orders[chat_id].pop(index)
    logs[chat_id].append(f"{update.message.from_user.username or update.message.from_user.first_name} removed: {removed_order}")
    logging.info(f"Order removed in chat_id {chat_id}: {removed_order}")

    # Delete the previous order list message
    if 'order_message_id' in context.chat_data and context.chat_data['order_message_id']:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.chat_data['order_message_id'])
        except Exception as e:
            logging.error(f"Failed to delete previous order list message in chat_id {chat_id}: {e}")

    # Update the order list message
    order_list = f"Order Chain: {chains[chat_id]}\n" + "\n".join(orders[chat_id])
    msg = await context.bot.send_message(chat_id=chat_id, text=order_list)
    context.chat_data['order_message_id'] = msg.message_id
    logging.info(f"Created new order list message in chat_id {chat_id}")


async def endchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chains:
        final_order_list = f"Final Order Chain: {chains[chat_id]}\n" + "\n".join([f"{i + 1} - {o}" for i, o in enumerate(orders[chat_id])])
        action_log = "\n".join(logs[chat_id])
        await context.bot.send_message(chat_id=chat_id, text=f"Action log:\n{action_log}")
        await context.bot.send_message(chat_id=chat_id, text=f"Order chain ended: {chains[chat_id]}")
        await context.bot.send_message(chat_id=chat_id, text=final_order_list)
        logging.info(f"Order chain ended in chat_id {chat_id} with topic: {chains[chat_id]}")
        del chains[chat_id]
        del orders[chat_id]
        del logs[chat_id]
        context.chat_data.pop('order_message_id', None)
    else:
        logging.warning(f"Endchain command received with no active chain in chat_id: {chat_id}")
        await context.bot.send_message(chat_id=chat_id, text="No active order chain to end.")

async def update_order_list_message(chat_id, context):
    order_list = f"Order Chain: {chains[chat_id]}\n" + "\n".join([f"{i + 1} - {o}" for i, o in enumerate(orders[chat_id])])

    if 'order_message_id' not in context.chat_data:
        context.chat_data['order_message_id'] = None

    if context.chat_data['order_message_id']:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=context.chat_data['order_message_id'],
                text=order_list
            )
            logging.info(f"Updated order list message in chat_id {chat_id}")
        except Exception as e:
            logging.error(f"Failed to edit message in chat_id {chat_id}: {e}")
            msg = await context.bot.send_message(chat_id=chat_id, text=order_list)
            context.chat_data['order_message_id'] = msg.message_id
            logging.info(f"Created new order list message in chat_id {chat_id}")
    else:
        msg = await context.bot.send_message(chat_id=chat_id, text=order_list)
        context.chat_data['order_message_id'] = msg.message_id
        logging.info(f"Created new order list message in chat_id {chat_id}")

async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chains:
        order_list = f"Order Chain: {chains[chat_id]}\n" + "\n".join(orders[chat_id])
        await context.bot.send_message(chat_id=chat_id, text=order_list)
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

if __name__ == '__main__':
    application = ApplicationBuilder().token(config.token).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('setchain', setchain))
    application.add_handler(CommandHandler('add', add))
    application.add_handler(CommandHandler('edit', edit))
    application.add_handler(CommandHandler('remove', remove))
    application.add_handler(CommandHandler('endchain', endchain))
    application.add_handler(CommandHandler('log', log))
    application.add_handler(CommandHandler('list', list_orders))

    application.add_handler(MessageHandler(~filters.COMMAND, log_message))

    logging.info("Bot started")
    application.run_polling()
    logging.info("Bot stopped")

 