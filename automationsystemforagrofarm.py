#this resp is made public temporarily  only for my visa interview. if you are not my visa officer you are not welcome here


import time
import requests
import board
import adafruit_dht
from gpiozero import OutputDevice


#   connect GPIO Pins
DHT_PIN = board.D4            # GPIO 4 (Data pin for DHT22)
COOLING_RELAY_PIN = 17       # GPIO 17 (Fans and Misters)
MED_PUMP_RELAY_PIN = 27      # GPIO 27 (Medication Pump)

# firm animal er jonno temparature and humidity hresholds
TEMP_MAX = 32.0              # °C e ase
HUMID_MAX = 65.0             # % e ase
HEAT_INDEX_MAX = 35.0         # °C danger zone

#google weather api(Backup)
API_KEY = "f1b9a8a04cdb32ce8b5f109a7710f1b3"
LAT = "23.162733"
LON = "91.186397"
URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

# HARDWARE er kaz
# Using gpiozero automatic and clean backup dibo
# relay module ulta kaz korle active high re false e change korbo
cooling_relay = OutputDevice(COOLING_RELAY_PIN, active_high=True, initial_value=False)
med_pump_relay = OutputDevice(MED_PUMP_RELAY_PIN, active_high=True, initial_value=False)

# dht22 sensor er kaz shuru
dht_sensor = adafruit_dht.DHT22(DHT_PIN)

#heat index er formula
def calculate_heat_index(T, R):
    """
    Calculates Heat Index in Celsius using the Rothfusz regression formula.
    T = Temperature in Celsius, R = Relative Humidity in %
    """
    # celsius to ferhenhite
    T_f = (T * 9/5) + 32
     
    # mild condition er laigga sutro
    hi_f = 0.5 * (T_f + 61.0 + ((T_f - 68.0) * 1.2) + (R * 0.094))
      #  heat index is high hoile eta apply koro
    if hi_f >= 80:
        hi_f = (-42.379 + 2.04901523 * T_f + 10.14333127 * R - 0.22475541 * T_f * R
                - 0.00683783 * T_f**2 - 0.05481717 * R**2 + 0.0122874 * T_f**2 * R
                + 0.0085282 * T_f * R**2 - 0.00000199 * T_f**2 * R**2)
         
    # celsius e abar result back
    hi_c = (hi_f - 32) * 5/9
    return round(hi_c, 2)

def get_sensor_data():
    """Attempts to read from the physical DHT22 sensor inside the shed."""
    try:
        temperature = dht_sensor.temperature
        humidity = dht_sensor.humidity
        if temperature is not None and humidity is not None:
            return round(temperature, 1), round(humidity, 1)
    except RuntimeError as error:
        # DHT sensors porte vhul korle eta crash handle korbe
        print(f"sensor read glitch: {error.args[0]}")
    except Exception as e:
        print(f"unexpected sensor error: {e}")
    return None, None
def get_backup_weather_data():
    """Fallback API call if the physical sensor fails entirely."""
    try:
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            temperature = data['main']['temp']
            humidity = data['main']['humidity']
            print("BACKUP ACTIVE hoise sensor e somossa.")
            return temperature, humidity
        else:
            print(f"weather API returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"backup API connection failed (Network Issue): {e}")
    return None, None

def manage_environmental_controls(trigger_on):
    """Turns systems ON or OFF based on threshold rules."""
    if trigger_on:
        cooling_relay.on()
        med_pump_relay.on()
        print("ALERT: Threshold crossed! Fans, misters, and medication pump are ON.")
    else:
                cooling_relay.off()
    med_pump_relay.off()
    print("environment stable. Automated systems are currently OFF.")

#automation loop
print(".")
print("automation start hyse")
print("monitoring temparature environment")
print(".")

try:
    while True:
        temp, humid = get_sensor_data()
        if temp is None or humid is None:
            temp, humid = get_backup_weather_data()
             
        if temp is not None and humid is not None:
            heat_index = calculate_heat_index(temp, humid)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Temp: {temp}°C | Humidity: {humid}% | Heat Index: {heat_index}°C")
             
            # Evaluate risk
            if temp > TEMP_MAX or humid > HUMID_MAX or heat_index > HEAT_INDEX_MAX:
                manage_environmental_controls(True)
            else:
                manage_environmental_controls(False)
        else:
            #  worst-case scenario: Hardware failed AND internet went down.
            print("failure: No reading from sensor OR backup API! System blind.")
             
         
        time.sleep(30)

except KeyboardInterrupt:
    print("\nShutting down automation loop cleanly...")
finally:
     
    print("System offline. Relays disengaged safely.")
