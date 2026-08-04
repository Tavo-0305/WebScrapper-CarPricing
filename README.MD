# Korean Used Car Deal Alert

Python scraper that monitors [Autobell Global](https://www.autobellglobal.com/) (Hyundai Glovis' used car export platform) for vehicles matching specific criteria — gasoline, automatic transmission, year and price thresholds — and sends real-time Telegram notifications when a new matching listing appears.

## How it works

1. `car_filter.py` queries Autobell Global's internal API directly (no browser automation needed) and filters results by fuel type, transmission, year, and price.
2. Previously notified cars are tracked in `seen_cars.json` to avoid duplicate alerts.
3. `telegram_bot.py` sends formatted notifications through a Telegram bot for each new match.

## Setup

1. Install dependencies:
```bash
   pip install -r requirements.txt
```

2. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and get your bot token.

3. Set the following environment variables:
```bash
   export TELEGRAM_BOT_TOKEN="your_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
```

4. Run:
```bash
   python car_filter.py
```

## Configuration

Filter values (max price, fuel type, transmission, minimum year) can be adjusted at the top of `car_filter.py`.

## License

MIT