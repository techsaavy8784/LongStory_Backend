from django_countries.data import COUNTRIES
import requests
from django.conf import settings
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_device(request):
    user_agent = request.user_agent
    device = "Other"
    
    if user_agent.is_mobile:
        device = "Mobile" 
    if user_agent.is_tablet:
        device = "Tablet" 
    if user_agent.is_pc:
        device = "PC" 
    return device



def get_country_code(country_name):
    for code, name in COUNTRIES:
        if name == country_name:
            return code
    return None


def get_country(country_code):
    for code, name in COUNTRIES:
        if code == country_code:
            return name
    return None

def fc_validate_address(address):
    result =  {
        "success": False,
        "postal_code": "",
        "message": ""
    }
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': settings.GOOGLE_API_KEY,
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        # Extract information about the address
        formatted_address = data['results'][0]['formatted_address']
        location = data['results'][0]['geometry']['location']

        print(f"Validated Address: {formatted_address}")
        print(f"Latitude: {location['lat']}, Longitude: {location['lng']}")
        
        # first_result = data.get('results', [])[0] if 'results' in data else None
        postal_code = None
        if 'results' in data and data['results']:
            # Extract postal code from the first result
            first_result = data['results'][0]
            

            for component in first_result.get('address_components', []):
                if 'postal_code' in component.get('types', []):
                    postal_code = component.get('long_name')
                    break

            if postal_code:
                print(f"Postal Code: ")
            else:
                print("Postal code not found for the given address.")
        
        print(postal_code)

        result["success"] = True
        result["postal_code"] = str(postal_code)
    else:
        print(f"Address validation failed. Status: {data['status']}")
        if 'error_message' in data:
            print(f"Error Message: {data['error_message']}")
            result["message"] = data["error_message"]
    return result
        

# # Replace 'YOUR_API_KEY' with your actual API key
# api_key = 'YOUR_API_KEY'
# address_to_validate = '1600 Amphitheatre Parkway, Mountain View, CA'

# validate_address(api_key, address_to_validate)