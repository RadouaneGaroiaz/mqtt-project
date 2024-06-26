sensor_positions = {
    'room1': {'lat': 48.825745818582114, 'lon': 2.267290496852181},
    'room2': {'lat': 51.5074, 'lon': -0.1278},
    'kitchen': {'lat': 40.7128, 'lon': -74.0060}
}

def generate_recommendations(sensor_id, statistics):
    recommendations = []
    if statistics['avg_temp'] > 25:
        recommendations.append(f"Recommandation: Refroidir la {sensor_id} avec la climatisation.")
    if statistics['avg_humidity'] > 60:
        recommendations.append(f"Recommandation: Utiliser un déshumidificateur dans la {sensor_id}.")
    if not recommendations:
        recommendations.append("Recommandation: Les conditions sont normales.")
    return recommendations