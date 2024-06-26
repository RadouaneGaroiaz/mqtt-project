import datetime
import numpy as np
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

client = MongoClient(os.getenv('MongoUrl'))
db = client['Mqtt-project']

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
        
        return {
            'avg_humidity': np.mean(humidity),
            'avg_temp': np.mean(temp),
            'min_humidity': np.min(humidity),
            'min_temp': np.min(temp),
            'max_humidity': np.max(humidity),
            'max_temp': np.max(temp),
            'std_humidity': np.std(humidity),
            'std_temp': np.std(temp)
        }
    return None

def get_sensor_status(sensor_id):
    collection = db[f'sensor_{sensor_id}']
    latest_entry = collection.find_one(sort=[('timestamp', -1)])
    
    if latest_entry:
        return latest_entry.get('status', 'Unknown')
    return 'No Data'

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
