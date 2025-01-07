from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restplus import Api, Resource
import os
import json
import requests
from bs4 import BeautifulSoup

# Flask application setup
app = Flask(__name__)
CORS(app)

# Set up Flask-RESTPlus for API documentation
api = Api(app, version='1.0', title='Prayer Times API', description='A simple API to fetch prayer times, countries, cities, and districts data.')
ns = api.namespace('api', description='Main API operations')

# JSON file loading dynamically
json_file_path = os.path.join(os.path.dirname(__file__), 'countries_cities_districts.json')
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# /get-countries API endpoint
@ns.route('/get-countries')
class GetCountries(Resource):
    def get(self):
        """
        Returns a list of available countries.
        """
        countries = [{"id": country, "name": country} for country in data.keys()]
        return jsonify(countries)

# /get-cities API endpoint
@ns.route('/get-cities')
class GetCities(Resource):
    def get(self):
        """
        Returns a list of cities for the given country.
        - country: The name of the country
        """
        country = request.args.get('country')
        if country not in data:
            return jsonify({"error": "Invalid country"}), 400

        cities = [{"id": city["id"], "name": city["name"]} for city in data[country]["cities"]]
        return jsonify(cities)

# /get-districts API endpoint
@ns.route('/get-districts')
class GetDistricts(Resource):
    def get(self):
        """
        Returns a list of districts for the given city.
        - country: The name of the country
        - cityId: The ID of the city
        """
        country = request.args.get('country')
        city_id = request.args.get('cityId')

        if country not in data:
            return jsonify({"error": "Invalid country"}), 400

        city = next((city for city in data[country]["cities"] if city["id"] == city_id), None)
        if not city:
            return jsonify({"error": "Invalid city"}), 400

        districts = [{"id": district["id"], "name": district["name"]} for district in city["districts"]]
        return jsonify(districts)

# /namaz-vakitleri API endpoint
@ns.route('/namaz-vakitleri')
class NamazVakitleri(Resource):
    def get(self):
        """
        Returns prayer times for the given city.
        - sehir: The name of the city (default: musul)
        - sehirId: The ID of the city
        - dil: Language option ('tr', 'en', 'ar') (default: tr)
        """
        sehir_adi = request.args.get('sehir', default='musul')
        sehir_id = request.args.get('sehirId', default=None)
        dil = request.args.get('dil', default='tr')

        if not sehir_adi or not sehir_id:
            return jsonify({"error": "Invalid city name or ID"}), 400

        url = f"https://namazvakitleri.diyanet.gov.tr/tr-TR/{sehir_id}/{sehir_adi}-icin-namaz-vakti"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Could not reach site: {str(e)}"}), 500

        soup = BeautifulSoup(response.content, "html.parser")
        prayer_times_div = soup.find("div", {"id": "today-pray-times-row"})

        if not prayer_times_div:
            return jsonify({"error": "Prayer times not found."}), 404

        prayer_times = {}
        for time_div in prayer_times_div.find_all("div", {"class": "tpt-cell"}):
            vakit_name = time_div.get("data-vakit-name")
            vakit_time = time_div.find("div", {"class": "tpt-time"}).text.strip()

            if dil == 'tr':
                translated_name = vakit_name
            elif dil == 'en':
                translated_name = translate_vakit_to_english(vakit_name)
            elif dil == 'ar':
                translated_name = translate_vakit_to_arabic(vakit_name)
            else:
                translated_name = vakit_name

            prayer_times[translated_name] = vakit_time

        return jsonify(prayer_times)

# Translation functions
def translate_vakit_to_english(vakit_name):
    translations = {
        "imsak": "Fajr",
        "gunes": "Sunrise",
        "ogle": "Dhuhr",
        "ikindi": "Asr",
        "aksam": "Maghrib",
        "yatsi": "Isha"
    }
    return translations.get(vakit_name, vakit_name)

def translate_vakit_to_arabic(vakit_name):
    translations = {
        "imsak": "الفجر",
        "gunes": "الشروق",
        "ogle": "الظهر",
        "ikindi": "العصر",
        "aksam": "المغرب",
        "yatsi": "العشاء"
    }
    return translations.get(vakit_name, vakit_name)

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
