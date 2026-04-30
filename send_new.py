import paho.mqtt.client as mqtt
import time
import numpy as np
import pandas as pd
import json
from matplotlib import pyplot as plt
import joblib
from datetime import datetime

import warnings
warnings.filterwarnings('ignore')

# All the functions required and parameters

# Defining parameters being used
peak_capacity_per_shift = 30000  # Define peak capacity here
num_months = 12
current_time = datetime.now()
time_now = current_time.hour

#-----------------------------------------------------------------------------------------------------------#

# 1. Shift information

class ShiftMonitor:
    def __init__(self, shift_duration_seconds=60):
        """
        Initializes the ShiftMonitor.

        Parameters:
        - shift_duration_seconds (int): Duration of each shift in seconds. Default is 60 seconds (1 minute).
        """
        self.start_time = datetime.now()
        self.shift_duration = shift_duration_seconds
        self.shift_cycle = 4  # Number of shifts in the cycle (1 to 4)
        self.start_shift = 1  # Starting shift

    def get_shift(self):
        """
        Calculates and retrieves the current shift based on the elapsed time.

        Returns:
        - shift (int): Current shift value (1 to 4).
        """
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.start_time).total_seconds()
        elapsed_shifts = int(elapsed_seconds // self.shift_duration)
        current_shift = ((self.start_shift - 1 + elapsed_shifts) % self.shift_cycle) + 1
        shifts = ['Morning', 'Afternoon', 'Evening', 'Night']
        return shifts[current_shift-1]

    def get_elapsed_time(self):
        """
        Retrieves the elapsed time since the ShiftMonitor was initialized.

        Returns:
        - elapsed_time (datetime.timedelta): Time elapsed since start.
        """
        current_time = datetime.now()
        return current_time - self.start_time
    
# Instantiate the class
shift_monitor = ShiftMonitor()

# Convert 'Shift' from categorical to numeric
shift = {"Morning":1,"Afternoon":2,"Evening":3,'Night':4}
#-----------------------------------------------------------------------------------------------------------#

# 2. Generating the production schedule
def generate_production_schedule(peak_capacity_per_shift, num_shifts=4):
    """Generates a simplified production schedule for one day."""
    shifts = ['Morning', 'Afternoon', 'Evening', 'Night']
    production = np.random.dirichlet(np.ones(num_shifts), size=1)[0] * peak_capacity_per_shift
    return pd.DataFrame({'Shift': shifts, 'Planned Production': production.astype(int)})

production_schedule = generate_production_schedule(peak_capacity_per_shift,4)

#-----------------------------------------------------------------------------------------------------------#

# 3. Real time data generation
def generate_real_time_data(current_time, production_schedule, peak_capacity_per_shift):
    """Generates simulated real-time production and energy consumption data."""
    current_shift =  shift_monitor.get_shift()   # get_current_shift(current_time)

    # Simulate production with more variability (example)
    planned_production = production_schedule.loc[production_schedule['Shift'] == current_shift, 'Planned Production'].values[0] / 8
    current_production = np.random.normal(planned_production, planned_production * 0.15)  # 15% variability

    # Simulate dynamic parameters (examples)
    pulp_quality = np.random.normal(75, 5) 
    basis_weight = np.random.normal(180, 10)
    drying_temp = np.random.normal(180, 5)
    nip_pressure = np.random.normal(1200, 100)
    drive_load = np.random.normal(70, 5)
    pump_flow = np.random.normal(25, 3)

    # Parameters for the energy consumption formula
    a, b = 0.8, -0.2
    c, d = 0.1, 1.1
    e, f = 0.05, 1.2
    g, h, i, j = 2, 0.8, 0.05, 180
    k, l, m, n = 0.3, -0.3, 0.02, 1200
    o, p = 5, 1.05
    q, r = 10, 1.1

    # Calculate current energy consumption using the formula (with simulated parameters)
    base_energy_consumption = (
        a * (pulp_quality ** b)
        + c * (basis_weight ** d)
        + e * (current_production ** f)
        + g * (drying_temp ** h) / (1 + np.exp(-i * (drying_temp - j)))
        + k * (nip_pressure ** l) / (1 + np.exp(m * (nip_pressure - n)))
        + o * (drive_load ** p)
        + q * (pump_flow ** r)
    ) * (1 + 0.05 * (current_shift == 'Night')) 

    # Introduce variability around the predicted energy with different low and high side factors
    low_side_factor = 0.8  # 5% decrease on the low side
    high_side_factor = 1.01  # 3% increase on the high side
    variability_factor = np.random.uniform(low_side_factor, high_side_factor)
    
    current_energy_consumption = base_energy_consumption * variability_factor

    # Occasional spikes (e.g., 5% chance of exceeding predicted energy by 10%)
    if np.random.rand() < 0.05:
        current_energy_consumption *= 1.1

    # Shift-based adjustment
    current_energy_consumption *= (1 + 0.05 * (current_shift == 'Night'))

    # Return all variables needed for prediction
    return {
        'PulpQuality': pulp_quality,
        'PaperBasisWeight': basis_weight,
        'SheetCountperRoll': current_production,  # Assuming sheet count is related to production
        'DryingTemperature': drying_temp,
        'NipPressure': nip_pressure,
        'ElectricalDriveLoad': drive_load,
        'PumpFlowRate': pump_flow,
        'Shift': current_shift,
        'Energy': current_energy_consumption
    }
    
#-----------------------------------------------------------------------------------------------------------#

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"  # Replace with your MQTT broker address
mqtt_topic = "energy_consumption"
mqtt_port = 1883

# Initialize MQTT Client
client = mqtt.Client()
client.connect(mqtt_broker,mqtt_port)

#-----------------------------------------------------------------------------------------------------------#

# Publish Real-time Data
while True:
    current_energy = generate_real_time_data(current_time,production_schedule,peak_capacity_per_shift)

    #real_time_data = generate_real_time_data(current_time, production_schedule_df, peak_capacity_per_shift, dynamic_prices)

    # Convert real-time data to JSON string
    json_data = json.dumps(current_energy)
    
    # Publish JSON data to MQTT
    client.publish(mqtt_topic, json_data)
    print(f"Published data:\n{json_data}")


    time.sleep(5)  # Publish every 30 second (adjust as needed)