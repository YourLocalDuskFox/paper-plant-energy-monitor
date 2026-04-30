# Real-Time Energy Monitoring (Paper Plant)

A Streamlit dashboard that pulls live energy telemetry from a paper towel production line over MQTT and flags anomalous consumption against a Random Forest baseline. Built for a INFO 4160 Industrial Internet of Things. Sensors → broker → model → operator screen.

## What it does

The plant publishes JSON messages to an MQTT topic with the current state of the line: pulp quality, basis weight, sheet count, temperature, nip pressure, drive load, pump flow, and the actual measured energy draw. The dashboard subscribes, runs each message through a trained classifier that predicts the *expected* energy band given the operating conditions, and shows a live chart with an alert when actual deviates from predicted.

The classifier is a Random Forest trained offline on historical plant data.

## Stack

- `paho-mqtt` for the MQTT client
- `scikit-learn` (Random Forest) for the model
- `streamlit` for the dashboard
- `joblib` for model persistence
- Public broker: `test.mosquitto.org:1883`

## Running it

```bash
pip install -r requirements.txt
streamlit run MP1_MQTT_Streamlit.py
```

You also need a publisher pushing to the `energy_consumption` topic. The `MP1.ipynb` notebook has the publisher code I used for testing. Run that in a separate terminal/kernel.

## What I struggled with

The ML itself was fairly easy once I had figured out which modeling style to use. However, getting the steamlit frontend to work with MQTT was a real challenge. The fix was using 'loop_start()' instead of 'loop_forever()' while pushing messages into st.session_state.

## Files

MP1_sub.py          the Streamlit dashboard, subscribes to MQTT and plots energy
send_new.py         simulates the paper plant, publishes JSON to the broker
MP1.ipynb           trains the Random Forest on em_data.csv, saves the model
em_data.csv         10,000 rows of historical plant telemetry (8 features + energy)
energy_model.joblib WILL HAVE TO RUN TRAINING DATA OFF THE CSV YOURSELF.
