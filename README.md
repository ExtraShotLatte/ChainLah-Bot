# ChainLah! - Your friendly chain message telegram bot 🤖

This Telegram bot allows users to create, manage, and log order chains within group chats. The bot supports adding, editing, and removing orders, as well as logging actions for auditing purposes.

## Features ✨

- Set a chain topic
- Add orders to the chain
- Edit existing orders
- Remove orders from the chain
- End the chain and display the final list of orders
- Log actions (add, edit, remove) and display the log
- Commands work seamlessly in group chats

## Commands 📋

- `/start` - Show instructions on how to use the bot
- `/setchain <chaintopic>` - Start a new order chain with the specified topic
- `/add <order>` - Add an order to the current chain
- `/edit <index> <new_order>` - Edit an order at the specified index
- `/remove <index>` - Remove an order at the specified index
- `/endchain` - End the current chain and display the final list of orders along with the action log
- `/log` - Display the current log of actions

## Setup 🛠️

1. Clone the repository:
    ```bash
    git clone https://github.com/ExtraShotLatte/ChainLah-Bot.git
    cd telegram-order-chain-bot
    ```

2. Create and activate a virtual environment:
    ```bash
    # MacOS or Linux
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python3 -m venv venv
    ./venv/scripts/activate
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `config.py` file and add your bot token (generated from bot father):
    ```python
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
    ```

5. Run the bot:
    ```bash
    python bot.py
    ```

## Usage 📊

1. Add the bot to a group chat and grant it admin privileges (necessary for deleting messages).
2. Use the commands as described above to manage your order chains.

## Example

- Set a chain topic:
    ```text
    /setchain Lunch Orders
    ```
    Response:
    ```text
    Chain started: Lunch Orders
    ```

- Add an order:
    ```text
    /add Pizza
    ```
    Response:
    ```text
    Order added: Pizza
    ```

- Edit an order:
    ```text
    /edit 1 Pasta
    ```
    Response:
    ```text
    Order at index 1 edited: Pasta
    ```

- Remove an order:
    ```text
    /remove 1
    ```
    Response:
    ```text
    Order at index 1 removed.
    ```

- End the chain and display the final list of orders and action log:
    ```text
    /endchain
    ```
    Response:
    ```text
    Order chain ended: Lunch Orders
    Action log:
    User1 added: Pizza
    User1 edited: Pizza -> Pasta
    User1 removed: Pasta

    Final Order Chain: Lunch Orders
    1 - Pasta
    ```

- Display the current action log:
    ```text
    /log
    ```
    Response:
    ```text
    Action log:
    User1 added: Pizza
    User1 edited: Pizza -> Pasta
    User1 removed: Pasta
    ```

## Contributing  🤝

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Thank You! 📜

Thank you for using Order Chain Bot! Enjoy seamless order management in your group chats. 🎉