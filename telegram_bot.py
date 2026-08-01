"""
Sends car alert notifications through a Telegram bot

Reads the bot token and chat ID from environment variables, so no
sensitive data lives in the code itself
"""

#Note: Some outputs are established to be in Spanish since the main user uses this language.

import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def format_car_message(car: dict) -> str:
    """
    Builds a readable, HTML-formatted message for a single car.
    """
    detail = f" {car['detail_model_name']}" if car.get("detail_model_name") else ""

    return (
        f"<b>{car['brand']} {car['model']}{detail}</b>\n"
        f"Año: {car['year']}\n"
        f"Kilometraje: {car['mileage']:,} km\n"
        f"Combustible: {car['fuel']}\n"
        f"Transmisión: {car['transmission']}\n"
        f"Precio: ${car['price_usd']:,} USD\n"
        f"<a href=\"{car['link']}\">Ver detalles</a>"
    )


def send_telegram_message(message: str) -> None:
    """
    Sends a single text message through the configured Telegram bot.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError(
            "Faltan las variables de entorno TELEGRAM_BOT_TOKEN y/o "
            "TELEGRAM_CHAT_ID. Defínelas antes de correr el script."
        )

    url = TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    response = requests.post(url, data=payload, timeout=15)
    response.raise_for_status()

    body = response.json()
    if not body.get("ok", False):
        raise RuntimeError(f"Telegram respondió con un error: {body}")


def notify_new_cars(cars: list) -> None:
    """
    Sends one Telegram message per new car found.
    If the list is empty, sends a short summary message instead.
    """
    if not cars:
        send_telegram_message("🔍 Revisión completada: no se encontraron autos nuevos esta vez.")
        return

    send_telegram_message(f"🚨 ¡Se encontraron {len(cars)} auto(s) nuevo(s)!")

    for car in cars:
        message = format_car_message(car)
        send_telegram_message(message)


if __name__ == "__main__":
    # Quick manual test: sends a fake car notification to confirm
    # the bot/token/chat_id setup works correctly.
    test_car = {
        "brand": "KIA",
        "model": "Morning",
        "detail_model_name": "All New Morning",
        "year": 2016,
        "mileage": 94663,
        "fuel": "Gasoline",
        "transmission": "Automatic",
        "price_usd": 2932,
        "link": "https://www.autobellglobal.com/usedcar/info/DV289614",
    }

    print("Enviando mensaje de prueba a Telegram...")
    send_telegram_message(format_car_message(test_car))
    print("Mensaje enviado. Revisa el chat de Telegram.")