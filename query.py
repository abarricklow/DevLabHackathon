import requests

# Geo-Json
# Daily data provide one data value to represent water conditions for the day.
# The continuous data collected each day, such as the daily mean, minimum, or maximum value.
url = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?f=json"

response = requests.get(url)

# Check if request works
if response.status_code == 200:
    data = response.json()  # converts JSON → Python dict
    
    print(data)  # see structure
    
    # Example: accessing fields
    for item in data.get("Feature", []):  # common in GeoJSON
        print(item)
else:
    print("Error:", response.status_code)