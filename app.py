import datetime
import threading
import streamlit as st
import pydeck as pdk
import plotly.graph_objects as go
import pandas as pd
from mqtt_handlers import setup_mqtt_client
from db_operations import compute_statistics, get_sensor_status, get_time_series_data
from utils import sensor_positions, generate_recommendations

def send_led_command(client, command):
    topic = "kitchen/topic"
    payload = command
    client.publish(topic, payload)
    print(f"Sent command '{command}' to topic '{topic}'")

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
    
    positions_df = pd.DataFrame(sensor_positions).T.reset_index().rename(columns={'index': 'sensor_id', 'lat': 'latitude', 'lon': 'longitude'})
    selected_sensor_pos = positions_df[positions_df['sensor_id'] == selected_sensor_id]

    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=zoom_level
    )

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=positions_df,
        get_position='[longitude, latitude]',
        get_radius=1000,
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

            recommendations = generate_recommendations(selected_sensor_id, stats)
            
            st.subheader('Recommandations')
            for rec in recommendations:
                st.write(rec)
            
            if st.button('Turn LED On'):
                send_led_command(mqtt_client, "ledOn")
            
            if st.button('Turn LED Off'):
                send_led_command(mqtt_client, "ledOff")
                
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
    mqtt_client = setup_mqtt_client()
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
    mqtt_thread.start()
    
    main()
