import requests

url = "https://www.autobellglobal.com/api/glovis/search/carFilterMobileList"

params = {
    "makerModelGrade": "",       # vacío = todas las marcas/modelos
    "fuels": "C004",              # C004 = Gasoline (según vimos en carFilterData)
    "yearsFrom": 2020,
    "yearsTo": 2026,
    "mileageFrom": 0,
    "mileageTo": 300000,
    "priceFrom": 0,
    "priceTo": 2000,               # <-- aquí pones el límite de $2000 de tu papá
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
    "page": 1,
    "size": 14,
    "countryCode": "CR",
    "isSellerLink": "false",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

response = requests.get(url, params=params, headers=headers)
print(response.status_code)
print(response.text[:3000])