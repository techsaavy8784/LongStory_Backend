# import pycountry

# def get_country_code(country_name):
#     try:
#         country = pycountry.countries.get(name=country_name)
#         if country:
#             return country.alpha_2
#         else:
#             return None  # Country not found
#     except Exception as e:
#         print(f"Error: {e}")
#         return None

import requests
from django.conf import settings


def get_shipstation_carriers():
    base_url = "https://ssapi.shipstation.com/carriers"
    headers = {
        'Authorization': f'Basic {settings.SHIPSTATION_API_KEY}:{settings.SHIPSTATION_API_SECRET}',
        'Content-Type': 'application/json',
    }

    response = requests.get(base_url, headers=headers)

    if response.status_code == 200:
        # Successfully retrieved carriers
        carriers = response.json()
        print("Carriers:")
        for carrier in carriers:
            print(f"{carrier['carrierId']}: {carrier['name']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        

import requests
import json
import base64

def fc_get_shipstation_rates(country, to_zip, weight, unit_w, dimension_l, dimension_w, dimension_h, unit_d):
    result = {
        "success": False,
        "rates": None,
        "message": ""
    }
    carrier_code = None
    # dimensions = dimension.split("*")
    if country == "US":
        carrier_code = settings.CARRIER_CODE_USA
    else:
        carrier_code = settings.CARRIER_CODE_GLOBAL
    base_url = "https://ssapi.shipstation.com/shipments/getrates"
    headers = {
        # 'Authorization': f'Basic {settings.SHIPSTATION_API_KEY}:{settings.SHIPSTATION_API_SECRET}',
        'Authorization': f'Basic {base64.b64encode(f"{settings.SHIPSTATION_API_KEY}:{settings.SHIPSTATION_API_SECRET}".encode()).decode()}',
        'Content-Type': 'application/json',
    }

    payload = {
        "carrierCode": carrier_code,
        "toCountry": country,
        # "serviceCode": service_code,
        "fromPostalCode": settings.FROM_ZIP,
        "toPostalCode": to_zip,
        "weight": {
            "value": weight,
            "units": unit_w  # You can adjust units as needed
        },
        # "dimensions": {
        #     "units": unit_d,
        #     "length": dimension_l,
        #     "width": dimension_w,
        #     "height": dimension_h
        # }
    }

    response = requests.post(base_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        # Successfully retrieved rates
        rates = response.json()
        result["success"] = True
        result["rates"] = rates
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        result["message"] = response.text
        
    return result

def fc_add_shipping_to_order(order_item, country, to_zip):
    result = {
        "success":False,
        "message": ""
    }
    variant = order_item.product.variants.filter(index=1)[0]
    shipping = variant.shipping
    weight = shipping.weight
    unit_w = shipping.unit_w
    dimension_l = shipping.dimension_l
    dimension_w = shipping.dimension_w
    dimension_h = shipping.dimension_h
    unit_d = shipping.unit_d
    
    get_shipstation_rates = fc_get_shipstation_rates(country, to_zip, weight, unit_w, dimension_l, dimension_w, dimension_h, unit_d)
    
    if get_shipstation_rates["success"] is False:
        result["message"] = get_shipstation_rates["message"]
        return result
    
    rates = get_shipstation_rates["rates"]
    
    rates = sorted(rates, key=lambda x: x["shipmentCost"], reverse=True)
    
    order_item.shipping_service_name = rates[0]["serviceName"]
    order_item.shipping_service_code = rates[0]["serviceCode"]
    order_item.shipping_rate = rates[0]["shipmentCost"]
    order_item.save()
    result["success"] = True
    return result

# views.py

# from django.http import JsonResponse
# import requests
# import json

# def fc_get_easyship_rates():
#     # Easyship API endpoint for getting rates
#     result = {
#         "success": False,
#         "data": None,
#         "message": None
#     }
#     easyship_api_url = "https://api.easyship.com/2023-01/rates"

#     # Easyship API credentials
#     api_key = settings.EASYSHIP_ACCESS_KEY

#     # Request headers
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {api_key}',
#     }

#     payload = {
#     "origin_address": {
#         "line_1": "9 S William St",
#         "state": "NY",
#         "country_alpha2": "US",
#         "postal_code": "10004",
#         "city": "New York",
#         "newKey": "New Value"
#     },
#     "destination_address": {
#         "country_alpha2": "US",
#         "line_1": "214 Hammock Blvd",
#         "state": "FL",
#         "city": "Clearwater",
#         "postal_code": "33761",
#         "contact_name": "Ronen Eizen"
#     },
#     "incoterms": "DDP",
#     "insurance": {
#         "is_insured": False
#     },
#     "courier_selection": {
#         "show_courier_logo_url": False,
#         "apply_shipping_rules": False
#     },
#     "shipping_settings": {
#         "units": {
#         "weight": "kg",
#         "dimensions": "cm"
#         }
#     },
#     "parcels": [
#         {
#         "box": {
#             "length": 20,
#             "width": 10,
#             "height": 14,
#             "slug": "null"
#         },
#         "items": [
#             {
#             "quantity": 1,
#             "hs_code": "85171400",
#             "description": "test",
#             "sku": "test",
#             "contains_battery_pi966": False,
#             "contains_battery_pi967": False,
#             "contains_liquids": False,
#             "origin_country_alpha2": "US",
#             "actual_weight": 1,
#             "declared_currency": "USD",
#             "declared_customs_value": 20
#             }
#         ],
#         "total_actual_weight": 1
#         }
#     ]
#     }

#     response = requests.post(easyship_api_url, json=payload, headers=headers)
#     # Check for a successful response (status code 200)
#     if response.status_code == 200:
#         result1 = response.text
#         # return JsonResponse(result)
#         print(result1)
#         result["success"] = True
#         result["data"] = result1
#     else:
#         # Handle errors or provide an appropriate response
#         # return JsonResponse({'error': 'Failed to get shipping rates'}, status=response.status_code)
#         result["message"] = response
        
#     return result

