import geopy
from geopy.geocoders import Nominatim
import ssl
import certifi
ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx

def geocode_address(address):
    geolocator = Nominatim(user_agent="nyc_property_sales", timeout=10)
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return location

# Example Usage:
address = "1211 6th Avenue, New York, NY"
coordinates = geocode_address(address)
print("Coordinates:", coordinates)