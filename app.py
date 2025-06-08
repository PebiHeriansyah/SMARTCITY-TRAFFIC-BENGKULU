import streamlit as st
import folium
import json
import pandas as pd
import logging
import openrouteservice
import requests
import os
from datetime import datetime
from streamlit_folium import st_folium
from joblib import load
from sklearn.impute import SimpleImputer

st.set_page_config(layout="wide")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmartCityApp")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'traffic_model_xgboost.joblib')
METADATA_PATH = os.path.join(BASE_DIR, 'model', 'model_metadata.json')

model = load(MODEL_PATH)
with open(METADATA_PATH) as f:
    metadata = json.load(f)
features = metadata['features']

class WeatherFetcher:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_weather(self, lat, lon):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric&lang=id"
            response = requests.get(url)
            data = response.json()
            if response.status_code == 200:
                return {
                    "Kota": data.get("name", "-"),
                    "Cuaca": data["weather"][0]["description"].capitalize(),
                    "Suhu": f"{data['main']['temp']}°C",
                    "Kelembapan": f"{data['main']['humidity']}%",
                    "Angin": f"{data['wind']['speed']} m/s"
                }
            else:
                return {"Error": data.get("message", "Gagal ambil data cuaca")}
        except Exception as e:
            logger.warning(f"Gagal mengambil cuaca: {e}")
            return {"Error": str(e)}

class RouteClient:
    def __init__(self, api_key):
        self.client = openrouteservice.Client(key=api_key)

    def get_route(self, coords, preference='fastest'):
        try:
            if not coords or len(coords) < 2:
                raise ValueError("Koordinat tidak valid")
            logger.info(f"Mengambil rute dengan preferensi '{preference}'")
            response = self.client.directions(
                coordinates=coords,
                profile='driving-car',
                preference=preference,
                format='geojson',
                instructions=False
            )
            return response
        except Exception as e:
            logger.error(f"Gagal mendapatkan rute: {str(e)}")
            return None

class RouteMetrics:
    def __init__(self, route_geojson):
        self.route = route_geojson

    def extract(self):
        try:
            feature = self.route['features'][0]
            props = feature['properties']
            summary = props.get('summary', {})
            return {
                'Durasi': f"{summary.get('duration', 0)/60:.1f} menit",
                'Jarak': f"{summary.get('distance', 0)/1000:.2f} km",
            }
        except Exception as e:
            logger.warning(f"Gagal ekstrak metrik: {str(e)}")
            return {'Durasi': 'Error', 'Jarak': 'Error'}

class RouteMap:
    def __init__(self, coords, geojson, color='red'):
        self.origin = coords[0]
        self.destination = coords[1]
        self.route_geojson = geojson
        self.color = color

    def generate(self):
        m = folium.Map(location=[self.origin[1], self.origin[0]], zoom_start=14)
        folium.GeoJson(
            self.route_geojson,
            name="Rute",
            style_function=lambda _: {
                'color': self.color,
                'weight': 5,
                'opacity': 0.7
            }
        ).add_to(m)
        folium.Marker([self.origin[1], self.origin[0]], tooltip="Asal",
                      icon=folium.Icon(color='green')).add_to(m)
        folium.Marker([self.destination[1], self.destination[0]], tooltip="Tujuan",
                      icon=folium.Icon(color='red')).add_to(m)
        return m

class SmartCityApp:
    def __init__(self):
        self.api_key = "5b3ce3597851110001cf624876268e6e79614e4db37552346c20305a"
        self.weather_api = "c5d852d31dcfdc06c5156f6753b81b81"
        self.weather = WeatherFetcher(self.weather_api)
        self.model = model
        self.imputer = SimpleImputer(strategy='mean')

        if 'points' not in st.session_state:
            st.session_state.points = []
        if 'routes' not in st.session_state:
            st.session_state.routes = {}
        if 'traffic_level_fastest' not in st.session_state:
            st.session_state.traffic_level_fastest = 0
        if 'traffic_level_alternative' not in st.session_state:
            st.session_state.traffic_level_alternative = 0

        self.points = st.session_state.points
        self.routes = st.session_state.routes
        self.client = RouteClient(self.api_key)

    def sidebar(self):
        st.sidebar.title("⚙ Pengaturan")
        st.sidebar.markdown("Klik dua titik di peta: Asal ➝ Tujuan")
        st.sidebar.write(f"🚦 Kemacetan Tercepat: {st.session_state.traffic_level_fastest}%")
        st.sidebar.write(f"🚦 Kemacetan Alternatif: {st.session_state.traffic_level_alternative}%")

        if st.sidebar.button("🔁 Reset Titik"):
            for key in ['points', 'routes', 'traffic_level_fastest', 'traffic_level_alternative']:
                st.session_state[key] = [] if isinstance(st.session_state.get(key), list) else 0
            st.rerun()

    def map_interaction(self):
        m = folium.Map(location=[-3.7932, 102.2651], zoom_start=14)
        m.add_child(folium.LatLngPopup())
        for idx, (lng, lat) in enumerate(self.points):
            label = "Asal" if idx == 0 else "Tujuan"
            color = "green" if idx == 0 else "red"
            folium.Marker([lat, lng], tooltip=label, icon=folium.Icon(color=color)).add_to(m)

        map_data = st_folium(m, height=600, width=1200)
        if map_data.get('last_clicked') and len(self.points) < 2:
            clicked = map_data['last_clicked']
            self.points.append((clicked['lng'], clicked['lat']))
            st.session_state.points = self.points

    def predict_traffic_level(self, route):
        try:
            feature = route['features'][0]
            props = feature['properties']
            summary = props.get('summary', {})
            segments = props.get('segments', [])

            hour = datetime.now().hour
            weekday = datetime.now().weekday()
            distance_km = summary.get('distance', 0) / 1000
            num_segments = len(segments)
            temperature = 30
            rain = 0

            input_dict = {
                'distance_km': distance_km,
                'num_segments': num_segments,
                'hour': hour,
                'weekday': weekday,
                'temperature': temperature,
                'rain': rain
            }

            X_input = pd.DataFrame([[input_dict.get(col, None) for col in features]], columns=features)
            X_imputed = pd.DataFrame(self.imputer.fit_transform(X_input), columns=features)
            pred = self.model.predict(X_imputed)[0]
            pred = max(0, min(int(pred), 100))
            return pred
        except Exception as e:
            logger.warning(f"Gagal prediksi kemacetan: {e}")
            return 0

    def search_routes(self):
        coords = self.points
        st.session_state.routes = {}

        rute_fastest = self.client.get_route(coords, 'fastest')
        rute_alternative = self.client.get_route(coords, 'shortest')

        def adjust_duration(route, traffic_level):
            try:
                feature = route['features'][0]
                summary = feature['properties'].get('summary', {})
                base_duration = summary.get('duration', 0)
                delay = base_duration * (traffic_level / 200)
                summary['duration'] = base_duration + delay
                return route
            except Exception as e:
                logger.warning(f"Error adjust_duration: {e}")
                return route

        if rute_fastest and rute_alternative:
            traffic_fastest = self.predict_traffic_level(rute_fastest)
            traffic_alternative = self.predict_traffic_level(rute_alternative)

            st.session_state.traffic_level_fastest = traffic_fastest
            st.session_state.traffic_level_alternative = traffic_alternative

            rute_fastest = adjust_duration(rute_fastest, traffic_fastest)
            rute_alternative = adjust_duration(rute_alternative, traffic_alternative)

            self.routes = {
                'Tercepat': rute_fastest,
                'Alternatif Bebas Macet': rute_alternative,
                'coords': coords
            }
            st.session_state.routes = self.routes
            st.success("✅ Rute berhasil ditemukan")
        else:
            st.error("❌ Gagal mengambil rute. Coba lagi!")

    def display_results(self):
        if not st.session_state.routes:
            return
        self.routes = st.session_state.routes
        st.subheader("📊 Hasil Rute")

        fastest_metrics = RouteMetrics(self.routes['Tercepat']).extract()
        alt_metrics = RouteMetrics(self.routes['Alternatif Bebas Macet']).extract()

        fastest_metrics['Durasi'] += f" (Kemacetan: {st.session_state.get('traffic_level_fastest', 0)}%)"
        alt_metrics['Durasi'] += f" (Kemacetan: {st.session_state.get('traffic_level_alternative', 0)}%)"

        df = pd.DataFrame({
            'Tercepat': fastest_metrics,
            'Alternatif Bebas Macet': alt_metrics
        }).T
        st.table(df)

        selected = st.radio("🧭 Pilih rute yang ditampilkan:", ['Tercepat', 'Alternatif Bebas Macet'], horizontal=True)
        color_map = {'Tercepat': 'red', 'Alternatif Bebas Macet': 'blue'}
        route_map = RouteMap(self.routes['coords'], self.routes[selected], color=color_map[selected]).generate()
    
        st_folium(route_map, height=600, width=1200)

        st.markdown("### 🌤 Cuaca di Titik Asal dan Tujuan")
        origin = self.routes['coords'][0]
        dest = self.routes['coords'][1]
        cuaca_asal = self.weather.get_weather(origin[1], origin[0])
        cuaca_tujuan = self.weather.get_weather(dest[1], dest[0])

        cuaca_df = pd.DataFrame({"Asal": cuaca_asal, "Tujuan": cuaca_tujuan})
        st.table(cuaca_df)

        with st.expander("⬇ Ekspor"):
            st.download_button("📄 Unduh GeoJSON",
                               data=json.dumps(self.routes[selected], indent=2),
                               file_name=f"rute_{selected.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
                               mime="application/json")

            df_points = pd.DataFrame({
                'Jenis': ['Asal', 'Tujuan'],
                'Longitude': [self.routes['coords'][0][0], self.routes['coords'][1][0]],
                'Latitude': [self.routes['coords'][0][1], self.routes['coords'][1][1]],
            })
            st.download_button("📄 Unduh Titik CSV", data=df_points.to_csv(index=False),
                               file_name="titik_rute.csv", mime="text/csv")

    def run(self):
        st.title("🛣️ Rekomendasi Rute dengan Prediksi Kemacetan Menggunakan AI di Kota Bengkulu")
        self.sidebar()
        self.map_interaction()

        if len(self.points) == 2:
            if st.button("🔍 Cari Rute"):
                self.search_routes()
            self.display_results()
        else:
            st.info("Klik dua kali titik di peta untuk pilih asal dan tujuan.")

if __name__ == '__main__':
    app = SmartCityApp()
    app.run()