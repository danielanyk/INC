import requests
from io import BytesIO
from auth.onemap_auth import get_access_token


def reverse_geocode(lat, lon, buffer=40):
    url = (
        f"https://www.onemap.gov.sg/api/public/revgeocode"
        f"?location={lat},{lon}&buffer={buffer}&addressType=All&otherFeatures=N"
    )
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("GeocodeInfo"):
            info = data["GeocodeInfo"][0]
            return {
                "BLOCK": info.get("BLOCK"),
                "ROAD": info.get("ROAD"),
                "BUILDING": info.get("BUILDING"),
                "POSTALCODE": info.get("POSTALCODE"),
            }
    return None


def generate_static_map(lat, lon, width=400, height=400):
    url = (
        f"https://www.onemap.gov.sg/api/staticmap/getStaticImage"
        f"?layerchosen=default&latitude={lat}&longitude={lon}"
        f"&zoom=17&width={width}&height={height}"
        f"&points=[{lat},{lon}]&color=255,0,0"
    )
    headers = {"Authorization": f"Bearer {get_access_token()}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BytesIO(response.content)
    return None
