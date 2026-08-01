"""
Script for consulting the Autobell Global (Hyundai Glovis) API's
"""
#Note: Some outputs are established to be in Spanish since the main user uses this language.

from telegram_bot import notify_new_cars
import requests
import time
import json
import os

#Data of interest:
MAX_PRICE = 2500       # Price in dolars
FUEL_TYPE = "C004"       # C004 = Gasoline 
TRANSMISSION = "C004"       # C004 = Automatic transmission 
MIN_YEAR = 2014            # models starting from this year
DESTINATION_COUNTRY = "CR"          # Looking for vehicles that can be exported to CR
PAGE_SIZE = 60         
HISTORY_FILE = "seen_cars.json"   # stores previously notified carKeys between runs

URL_BASE = "https://www.autobellglobal.com/api/glovis/search/carFilterMobileList"
URL_COUNT = "https://www.autobellglobal.com/api/glovis/search/carFilterCount"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def build_params(page: int) -> dict:
    """
    Builds a dictionary with parameters for the petition to the API
    """
    return {
        "makerModelGrade": "",       # all models
        "fuels": FUEL_TYPE,
        "transmission": TRANSMISSION,  
        "yearsFrom": MIN_YEAR,
        "yearsTo": 2026,
        "mileageFrom": 0,
        "mileageTo": 300000,
        "priceFrom": 0,
        "priceTo": MAX_PRICE,
        "isInspected": "false",
        "isPromotion": "false",
        "isAutobellStock": "false",
        "isKcar": "false",
        "isCar360View": "false",
        "isOv": "false",
        "isCarStockDV": "false",
        "isCarStockWeeky": "false",
        "isSellerCarRecommend": "false",
        "searchKeyword": "",
        "searchType": "",
        "orderBy": "recommend",
        "page": page,
        "size": PAGE_SIZE,
        "countryCode": DESTINATION_COUNTRY,
        "isSellerLink": "false",
    }


def obtain_expected_count() -> int:
    """
    Query the count endpoint (the same one the website uses to display
    "X Units in Total") to determine the total number of cars to expect.
    This serves as a security check against pagination.
    """
    params = {
        "mileageFrom": 0,
        "mileageTo": 300000,
        "yearsFrom": MIN_YEAR,
        "yearsTo": 2026,
        "priceFrom": 0,
        "priceTo": MAX_PRICE,
        "fuels": FUEL_TYPE,
        "transmission": TRANSMISSION, 
        "countryCode": DESTINATION_COUNTRY,
    }
    response = requests.get(URL_COUNT, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    body = response.json()

    if not body.get("success", False):
        raise RuntimeError(f"La API de conteo respondió sin éxito: {body}")

    data = body.get("data")

    if isinstance(data, list):
        return data[0]

    return data


def obtain_car_pages(page: int) -> list:
    """
    Requests a page of results from the API and returns the list of cars.
    """
    params = build_params(page)
    response = requests.get(URL_BASE, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    body = response.json()

    if not body.get("success", False):
        raise RuntimeError(f"La API respondió sin éxito: {body}")

    return body.get("data", [])


def obtain_relevat_data(raw_car_data: dict) -> dict:
    """
    Extracts only relevant data 
    """
    return {
        "carKey": raw_car_data.get("carKey"),
        "brand": raw_car_data.get("makerName"),
        "model": raw_car_data.get("modelName"),
        "detail_model_name": raw_car_data.get("modelDetailName"),
        "year": raw_car_data.get("year"),
        "mileage": raw_car_data.get("mileage"),
        "price_usd": raw_car_data.get("salePrice"),
        "fuel": raw_car_data.get("fuelTypeName") or raw_car_data.get("carFuelName"),
        "transmission": raw_car_data.get("gearBoxName") or raw_car_data.get("transmissionName"),
        "link": f"https://www.autobellglobal.com/usedcar/info/{raw_car_data.get('carKey')}",
    }


def obtain_all_cars() -> list:
    """
    Iterates through all result pages until the API stops
    returning cars, and returns the complete, simplified list.

    Includes two safety checks to detect unexpected API
    behavior (e.g., repeating results):
      1. Stops if the cumulative total exceeds the expected count.
      2. Stops if a previously seen carKey (duplicate) appears.
    """
    expected_count = obtain_expected_count()
    print(f"La API reporta un total esperado de {expected_count} autos.\n")

    all_cars = []
    checked_keys = set()
    pages = 1

    while True:
        raw_cars = obtain_car_pages(pages)

        if not raw_cars:
            break  # no more results

        for raw_car_data in raw_cars:
            key = raw_car_data.get("carKey")

            if key in checked_keys:
                raise RuntimeError(
                    f"Se encontró un carKey duplicado ({key}) en la página {pages}. "
                    "Esto sugiere un problema con la paginación (posiblemente el tamaño "
                    "de página no es soportado por la API). Deteniendo por seguridad."
                )

            checked_keys.add(key)
            filtered_car = obtain_relevat_data(raw_car_data)

            # Double verification: Transmission info is not always true 
            if filtered_car["transmission"] != "Automatic":
                print(
                    f"Aviso!!!: {key} vino con transmisión "
                    f"'{filtered_car['transmission']}' en vez de 'Automatic'. "
                    "El filtro de transmisión en la URL podría no estar funcionando "
                    "como se espera. Se omite este car de los resultados."
                )
                continue

            all_cars.append(filtered_car)

        print(f"Página {pages}: {len(raw_cars)} autos obtenidos "
              f"(total acumulado: {len(all_cars)} / esperado: {expected_count})")

        if len(all_cars) > expected_count:
            raise RuntimeError(
                f"El total acumulado ({len(all_cars)}) superó el conteo "
                f"esperado por la API ({expected_count}). Deteniendo por seguridad: "
                "algo no está funcionando como se espera."
            )

        pages += 1
        time.sleep(1)  # Pause between requests

    return all_cars

def load_history() -> set:
    """
    Loads the set of previously notified carKeys from the history file.
    If the file doesn't exist yet (first run), returns an empty set.
    """
    if not os.path.exists(HISTORY_FILE):
        return set()

    with open(HISTORY_FILE, "r", encoding="utf-8") as file:
        content = json.load(file)
        return set(content.get("notified_car_keys", []))


def save_history(notified_keys: set) -> None:
    """Saves the updated set of notified carKeys to the history file."""
    content = {"notified_car_keys": sorted(notified_keys)}

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(content, file, indent=2, ensure_ascii=False)


def split_new_and_seen(cars: list, history: set) -> tuple:
    """
    Splits the car list into two: cars already in history (previously
    notified) and new cars (to be notified now).
    """
    new_cars = [car for car in cars if car["carKey"] not in history]
    seen_cars = [car for car in cars if car["carKey"] in history]

    return new_cars, seen_cars

if __name__ == "__main__":
    print(f"Buscando autos de gasolina con precio <= ${MAX_PRICE} USD...\n")

    cars = obtain_all_cars()

    print(f"\nTotal de autos encontrados que cumplen los filtros: {len(cars)}\n")

    history = load_history()
    new_cars, seen_cars = split_new_and_seen(cars, history)

    print(f"Autos ya notificados anteriormente (se ignoran): {len(seen_cars)}")
    print(f"Autos NUEVOS (pendientes de notificar): {len(new_cars)}\n")

    notify_new_cars(new_cars)

    # Update history with ALL cars matching current filters (new + seen),
    # so the next run recognizes all of them as "already notified".
    updated_keys = history | {car["carKey"] for car in cars}
    save_history(updated_keys)

    print(f"\nHistorial actualizado y guardado en '{HISTORY_FILE}' "
          f"({len(updated_keys)} carKeys en total).")