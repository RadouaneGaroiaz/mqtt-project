import datetime
import json
import os
import threading

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
import paho.mqtt.client as mqtt
import pydeck as pdk

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MongoUrl'))
db = client['Mqtt-project']

# MQTT callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe([
        ("room1/topic", 0),
        ("room2/topic", 0),
        ("kitchen/topic", 0),
        # Add more sensors/topics as needed
    ])

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        payload['timestamp'] = datetime.datetime.now().isoformat()
        sensor_id = msg.topic.split("/")[0]
        collection = db[f'sensor_{sensor_id}']
        payload['position'] = sensor_id
        collection.insert_one(payload)
        print("Inserted data into MongoDB")
    except Exception as e:
        print(f"Error inserting into MongoDB: {e}")

# MQTT client setup
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("51.38.185.58", 1883, 60)

# Function to compute statistics
def compute_statistics(sensor_id, start_time, end_time):
    collection = db[f'sensor_{sensor_id}']
    query = {
        'timestamp': {
            '$gte': start_time.isoformat(),
            '$lte': end_time.isoformat()
        }
    }
    cursor = collection.find(query)
    
    data = [doc['data'] for doc in cursor]
    
    if data:
        humidity = [entry['humidity'] for entry in data]
        temp = [entry['temp'] for entry in data]
        
        avg_humidity = np.mean(humidity)
        avg_temp = np.mean(temp)
        min_humidity = np.min(humidity)
        min_temp = np.min(temp)
        max_humidity = np.max(humidity)
        max_temp = np.max(temp)
        std_humidity = np.std(humidity)
        std_temp = np.std(temp)
        
        return {
            'avg_humidity': avg_humidity,
            'avg_temp': avg_temp,
            'min_humidity': min_humidity,
            'min_temp': min_temp,
            'max_humidity': max_humidity,
            'max_temp': max_temp,
            'std_humidity': std_humidity,
            'std_temp': std_temp
        }
    else:
        return None

# Function to get sensor status
def get_sensor_status(sensor_id):
    collection = db[f'sensor_{sensor_id}']
    latest_entry = collection.find_one(sort=[('timestamp', -1)])
    
    if latest_entry:
        return latest_entry.get('status', 'Unknown')
    else:
        return 'No Data'
    
# Function to get time series data
def get_time_series_data(sensor_id, start_time, end_time):
    collection = db[f'sensor_{sensor_id}']
    
    query = {
        'timestamp': {
            '$gte': start_time.isoformat(),
            '$lte': end_time.isoformat()
        }
    }
    
    cursor = collection.find(query)
    timestamps = []
    humidity = []
    temp = []
    
    for doc in cursor:
        timestamps.append(doc['timestamp'])
        humidity.append(doc['data']['humidity'])
        temp.append(doc['data']['temp'])
    
    return pd.DataFrame({'timestamp': timestamps, 'humidity': humidity, 'temp': temp})

def generate_recommendations(sensor_id, statistics):
    recommendations = []
    if statistics['avg_temp'] > 25:
        recommendations.append(f"Recommandation: Refroidir la {sensor_id} avec la climatisation.")
    if statistics['avg_humidity'] > 60:
        recommendations.append(f"Recommandation: Utiliser un déshumidificateur dans la {sensor_id}.")
    if not recommendations:
        recommendations.append("Recommandation: Les conditions sont normales.")
    return recommendations

# Sensor positions (randomly generated for demonstration purposes)
sensor_positions = {
    'room1': {'lat': 48.825745818582114, 'lon': 2.267290496852181},  # Paris coordinates  48.825745818582114, 2.267290496852181
    'room2': {'lat': 51.5074, 'lon': -0.1278},  # London coordinates
    'kitchen': {'lat': 40.7128, 'lon': -74.0060}  # New York coordinates
}

# Streamlit interface
def main():
    st.title('Analyse des données de capteurs')
    
    selected_sensor_id = st.selectbox('Choisir le capteur', sensor_positions.keys())
    
    start_date = st.date_input('Date de début', datetime.date.today() - datetime.timedelta(days=7))
    end_date = st.date_input('Date de fin', datetime.date.today())
    
    if selected_sensor_id:
        lat = sensor_positions[selected_sensor_id]['lat']
        lon = sensor_positions[selected_sensor_id]['lon']
        zoom_level = 12
    else:
        lat = 0
        lon = 0
        zoom_level = 2
    
    # Create a DataFrame with sensor positions
    positions_df = pd.DataFrame(sensor_positions).T.reset_index().rename(columns={'index': 'sensor_id', 'lat': 'latitude', 'lon': 'longitude'})
    
    # Highlight the selected sensor
    selected_sensor_pos = positions_df[positions_df['sensor_id'] == selected_sensor_id]

    # Create the pydeck map
    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=zoom_level
    )

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=positions_df,
        get_position='[longitude, latitude]',
        get_radius=1000,  # Set radius to visualize markers clearly
        get_fill_color='[255, 0, 0, 160]',
        pickable=True
    )

    tool_tip = {"html": "Sensor ID:<br/> <b>{sensor_id}</b> ", "style": {"backgroundColor": "steelblue", "color": "white"}}

    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tool_tip)

    st.pydeck_chart(r)
    
    if start_date <= end_date:
        start_time = datetime.datetime.combine(start_date, datetime.time.min)
        end_time = datetime.datetime.combine(end_date, datetime.time.max)
        
        stats = compute_statistics(selected_sensor_id, start_time, end_time)
        status = get_sensor_status(selected_sensor_id)

        st.subheader(f'Statut du capteur {selected_sensor_id}')
        st.write(f"Statut: {status}")

        if stats:
            st.subheader(f'Statistiques pour {selected_sensor_id}')
            st.write(f"Moyenne de l'humidité: {stats['avg_humidity']:.2f}")
            st.write(f"Moyenne de la température: {stats['avg_temp']:.2f}")
            st.write(f"Min de l'humidité: {stats['min_humidity']:.2f}")
            st.write(f"Min de la température: {stats['min_temp']:.2f}")
            st.write(f"Max de l'humidité: {stats['max_humidity']:.2f}")
            st.write(f"Max de la température: {stats['max_temp']:.2f}")
            st.write(f"Écart type de l'humidité: {stats['std_humidity']:.2f}")
            st.write(f"Écart type de la température: {stats['std_temp']:.2f}")

            # Generate recommendations
            recommendations = generate_recommendations(selected_sensor_id, stats)
            
            st.subheader('Recommandations')
            for rec in recommendations:
                st.write(rec)
                
            # Plot time series data
            time_series_data = get_time_series_data(selected_sensor_id, start_time, end_time)
            
            if not time_series_data.empty:
                st.subheader('Graphiques des données')
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(x=time_series_data['timestamp'], y=time_series_data['temp'], mode='lines', name='Température'))
                fig.add_trace(go.Scatter(x=time_series_data['timestamp'], y=time_series_data['humidity'], mode='lines', name='Humidité'))
                
                fig.update_layout(title='Température et Humidité au fil du temps',
                                  xaxis_title='Timestamp',
                                  yaxis_title='Valeurs',
                                  legend_title='Paramètres')
                
                st.plotly_chart(fig)
            else:
                st.write(f"Aucune donnée disponible pour {selected_sensor_id} entre {start_time} et {end_time}")
        else:
            st.write(f"Aucune donnée disponible pour {selected_sensor_id} entre {start_time} et {end_time}")
    else:
        st.error('Erreur: La date de début doit être antérieure à la date de fin.')

if __name__ == '__main__':
    # Start the MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=mqttc.loop_forever)
    mqtt_thread.start()
    
    # Run the Streamlit app
    main()
