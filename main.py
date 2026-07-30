"""
Consulta la API interna de Autobell Global (Hyundai Glovis) y devuelve
la lista de autos de gasolina con precio menor o igual al máximo definido.
"""
import requests
import time

#Filtros básicos:
PRECIO_MAXIMO = 2000       # Dólares
COMBUSTIBLE = "C004"       # C004 = Gasolina 
TRANSMISION = "C004"       # C004 = Automatico 
MIN_YEAR = 2014            # Año mínimo
PAIS_ENVIO = "CR"          # El envío debe estar disponible hacia Costa Rica
TAMANO_PAGINA = 60         

URL_BASE = "https://www.autobellglobal.com/api/glovis/search/carFilterMobileList"
URL_CONTEO = "https://www.autobellglobal.com/api/glovis/search/carFilterCount"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def construir_parametros(pagina: int) -> dict:
    """Arma el diccionario de parámetros para la petición a la API."""
    return {
        "makerModelGrade": "",       # vacío, busco todas las marcas/modelos
        "fuels": COMBUSTIBLE,
        "transmission": TRANSMISION,  
        "yearsFrom": MIN_YEAR,
        "yearsTo": 2026,
        "mileageFrom": 0,
        "mileageTo": 300000,
        "priceFrom": 0,
        "priceTo": PRECIO_MAXIMO,
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
        "page": pagina,
        "size": TAMANO_PAGINA,
        "countryCode": PAIS_ENVIO,
        "isSellerLink": "false",
    }


def obtener_conteo_esperado() -> int:
    """
    Consulta el endpoint de conteo (el mismo que usa la web para mostrar
    "X Units in Total") para saber cuántos autos esperar en total.
    Sirve como validación de seguridad contra la paginación.
    """
    params = {
        "mileageFrom": 0,
        "mileageTo": 300000,
        "yearsFrom": MIN_YEAR,
        "yearsTo": 2026,
        "priceFrom": 0,
        "priceTo": PRECIO_MAXIMO,
        "fuels": COMBUSTIBLE,
        "transmission": TRANSMISION,  # confirmado: "transmission" (singular)
        "countryCode": PAIS_ENVIO,
    }
    respuesta = requests.get(URL_CONTEO, params=params, headers=HEADERS, timeout=15)
    respuesta.raise_for_status()
    cuerpo = respuesta.json()

    if not cuerpo.get("success", False):
        raise RuntimeError(f"La API de conteo respondió sin éxito: {cuerpo}")

    dato = cuerpo.get("data")

    if isinstance(dato, list):
        return dato[0]

    return dato


def obtener_autos_pagina(pagina: int) -> list:
    """Pide una página de resultados a la API y devuelve la lista de autos."""
    params = construir_parametros(pagina)
    respuesta = requests.get(URL_BASE, params=params, headers=HEADERS, timeout=15)
    respuesta.raise_for_status()
    cuerpo = respuesta.json()

    if not cuerpo.get("success", False):
        raise RuntimeError(f"La API respondió sin éxito: {cuerpo}")

    return cuerpo.get("data", [])


def simplificar_auto(auto_crudo: dict) -> dict:
    """Extrae solo los campos que interesan de cada auto."""
    return {
        "carKey": auto_crudo.get("carKey"),
        "marca": auto_crudo.get("makerName"),
        "modelo": auto_crudo.get("modelName"),
        "detalle_modelo": auto_crudo.get("modelDetailName"),
        "anio": auto_crudo.get("year"),
        "kilometraje": auto_crudo.get("mileage"),
        "precio_usd": auto_crudo.get("salePrice"),
        "combustible": auto_crudo.get("fuelTypeName") or auto_crudo.get("carFuelName"),
        "transmision": auto_crudo.get("gearBoxName") or auto_crudo.get("transmissionName"),
        "link": f"https://www.autobellglobal.com/usedcar/info/{auto_crudo.get('carKey')}",
    }


def obtener_todos_los_autos() -> list:
    """
    Recorre todas las páginas de resultados hasta que la API deje de
    devolver autos, y regresa la lista completa ya simplificada.

    Incluye dos validaciones de seguridad para detectar si la API se
    comporta de forma inesperada (por ejemplo, repitiendo resultados):
      1. Se detiene si el total acumulado supera el conteo esperado.
      2. Se detiene si aparece un carKey ya visto (duplicado).
    """
    conteo_esperado = obtener_conteo_esperado()
    print(f"La API reporta un total esperado de {conteo_esperado} autos.\n")

    todos_los_autos = []
    claves_vistas = set()
    pagina = 1

    while True:
        autos_crudos = obtener_autos_pagina(pagina)

        if not autos_crudos:
            break  # ya no hay más resultados

        for auto_crudo in autos_crudos:
            clave = auto_crudo.get("carKey")

            if clave in claves_vistas:
                raise RuntimeError(
                    f"Se encontró un carKey duplicado ({clave}) en la página {pagina}. "
                    "Esto sugiere un problema con la paginación (posiblemente el tamaño "
                    "de página no es soportado por la API). Deteniendo por seguridad."
                )

            claves_vistas.add(clave)
            auto_simplificado = simplificar_auto(auto_crudo)

            # Doble verificación: A veces la transmisión no coincide 
            # transmisión automática, confirmamos con el dato real del auto,
            # por si el parámetro de la URL no fuera el correcto.
            if auto_simplificado["transmision"] != "Automatic":
                print(
                    f"Aviso!!!: {clave} vino con transmisión "
                    f"'{auto_simplificado['transmision']}' en vez de 'Automatic'. "
                    "El filtro de transmisión en la URL podría no estar funcionando "
                    "como se espera. Se omite este auto de los resultados."
                )
                continue

            todos_los_autos.append(auto_simplificado)

        print(f"Página {pagina}: {len(autos_crudos)} autos obtenidos "
              f"(total acumulado: {len(todos_los_autos)} / esperado: {conteo_esperado})")

        if len(todos_los_autos) > conteo_esperado:
            raise RuntimeError(
                f"El total acumulado ({len(todos_los_autos)}) superó el conteo "
                f"esperado por la API ({conteo_esperado}). Deteniendo por seguridad: "
                "algo no está funcionando como se espera."
            )

        pagina += 1
        time.sleep(1)  # Pausa entre peticiones

    return todos_los_autos


if __name__ == "__main__":
    print(f"Buscando autos de gasolina con precio <= ${PRECIO_MAXIMO} USD...\n")

    autos = obtener_todos_los_autos()

    print(f"\nTotal de autos encontrados: {len(autos)}\n")

    for auto in autos:
        print(
            f"{auto['marca']} {auto['modelo']} {auto['detalle_modelo'] or ''} "
            f"({auto['anio']}) - {auto['kilometraje']} km - "
            f"${auto['precio_usd']} - {auto['link']}"
        )