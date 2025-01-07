from flask import Flask, jsonify, request
from flask_cors import CORS  # CORS'u ekleyin
import os
import json
import requests
from bs4 import BeautifulSoup

# Flask uygulamasını oluştur
app = Flask(__name__)
CORS(app)  # CORS'u etkinleştirin

# JSON dosyasını dinamik olarak yükle
json_file_path = os.path.join(os.path.dirname(__file__), 'countries_cities_districts.json')
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# /get-countries API endpoint
@app.route('/get-countries', methods=['GET'])
def get_countries():
    countries = [{"id": country, "name": country} for country in data.keys()]
    return jsonify(countries)

# /get-cities API endpoint
@app.route('/get-cities', methods=['GET'])
def get_cities():
    country = request.args.get('country')
    if country not in data:
        return jsonify({"error": "Geçersiz ülke"}), 400

    cities = [{"id": city["id"], "name": city["name"]} for city in data[country]["cities"]]
    return jsonify(cities)

# /get-districts API endpoint
@app.route('/get-districts', methods=['GET'])
def get_districts():
    country = request.args.get('country')
    city_id = request.args.get('cityId')

    if country not in data:
        return jsonify({"error": "Geçersiz ülke"}), 400

    city = next((city for city in data[country]["cities"] if city["id"] == city_id), None)
    if not city:
        return jsonify({"error": "Geçersiz şehir"}), 400

    districts = [{"id": district["id"], "name": district["name"]} for district in city["districts"]]
    return jsonify(districts)

# /namaz-vakitleri API endpoint
@app.route('/namaz-vakitleri', methods=['GET'])
def namaz_vakitleri():
    sehir_adi = request.args.get('sehir', default='musul')
    sehir_id = request.args.get('sehirId', default=None)
    dil = request.args.get('dil', default='tr')

    if not sehir_adi or not sehir_id:
        return jsonify({"error": "Geçersiz şehir adı veya id'si"}), 400

    url = f"https://namazvakitleri.diyanet.gov.tr/tr-TR/{sehir_id}/{sehir_adi}-icin-namaz-vakti"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Siteye erişilemedi: {str(e)}"}), 500

    soup = BeautifulSoup(response.content, "html.parser")
    prayer_times_div = soup.find("div", {"id": "today-pray-times-row"})

    if not prayer_times_div:
        return jsonify({"error": "Namaz vakitleri bulunamadı."}), 404

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

# Vakit isimlerini İngilizce'ye çevir
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

# Vakit isimlerini Arapça'ya çevir
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
