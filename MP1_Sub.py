import paho.mqtt.client as mqtt
import time
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import json
import streamlit as st
import joblib

import warnings
warnings.filterwarnings('ignore')

BROKER_ADDRESS = "test.mosquitto.org"
PORT = 1883
TOPIC = "energy_consumption"

latest_data_global = None
data_history_global = []
update_flag_global = False

def init_session_state():
    if "latest_data" not in st.session_state:
        st.session_state.latest_data = None
    if "data_history" not in st.session_state:
        st.session_state.data_history = []
    if "update_flag" not in st.session_state:
        st.session_state.update_flag = False

init_session_state()

client = mqtt.Client()

message = []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully. Subscribing to topic...")
        client.subscribe(TOPIC)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, message):
    global latest_data_global, data_history_global, update_flag_global
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        latest_data_global = payload
        data_history_global.append(payload)
        update_flag_global = True
        print("message received " ,str(message.payload.decode("utf-8")))
        print("message topic=",message.topic)
        print("message qos=",message.qos)
        print("message retain flag=",message.retain)
    except json.JSONDecodeError:
        print("Error decoding JSON")

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

print("connecting to broker")
client.connect(BROKER_ADDRESS, PORT)

client.loop_start()


loaded_model = joblib.load("MP1_1.6.1.joblib")












col1, col2 = st.columns(2)

with col1:
    st.header("Last Data Point")
    # Create placeholders for dynamic content
    data_placeholder = st.empty()
    
with col2:
    plot_placeholder = st.empty()
    # Store energy data points to be plotted
    plot_container = []
    st.header("Plot all Data")
    
# UI refresh loop: Set a timer to refresh the UI every 1 second
while True:
    # Polling mechanism: Check global update flag and update session state if true
    if update_flag_global:
        # Transfer global values to session state
        st.session_state.latest_data = latest_data_global
        st.session_state.data_history = data_history_global
        st.session_state.update_flag = True

        # Reset the global flag
        update_flag_global = False
        
    if st.session_state.latest_data: # If there is a reading
        # Update the placeholder with the new data
        with data_placeholder.container():
            st.json(latest_data_global)
            
        with plot_placeholder.container():
            for i in st.session_state.data_history:
                plot_container.append(i["Energy"])
            
            # Limit the plot to the most recent window_size data points
            window_size = (10) 

            if len(plot_container) > window_size:
                points = plot_container[-window_size:]
            else:
                points = plot_container   # Till 10 points are collected
            
            # Plot the line chart
            st.line_chart(
                points,
                x_label="Time",
                y_label="Temperature (Celsius)",
                width=500,
                height=200,
                use_container_width=False,
            )
        
    # Wait a bit
    time.sleep(1)
