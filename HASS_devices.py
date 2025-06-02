import requests
import json
import time
import threading
from my_signal import MySignal
import re


class HomeAssistantSwitchSummary:
    def __init__(self, url, api_token):
        self.signal = MySignal()
        self.url = url
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        self.devices = []
        self.switch_state_summary = {}
        self.extracted_numbers = {}
        self.running = True
        self.unavailable_rooms = []

    def _request(self, method, endpoint, data=None, action=None):
        """Helper method to handle HTTP requests."""
        url = f"{self.url}{endpoint}"
        print (url, '<----- url')
        #action_ = endpoint.split('/')[-1]
        #print (action, 'actions')
        try:
            rm_name_ = None
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
                resp_ = response.json()
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
                #print (data, '<----- data')
                rm_name_ = self._extract_room_name(data['entity_id']).split(' ')[1]
                resp_ = response.status_code
            response.raise_for_status()  # Check for errors in the response
                
            #resp_ = response.json() if response.status_code == 200 else None
            #print (resp_, '<----- resp_')
            return [resp_, rm_name_]
        except requests.exceptions.RequestException as e:
            #print(f"HTTP error: {e}")
            #print ('http error')
            if data:
                rm_name_ = self._extract_room_name(data['entity_id']).split(' ')[1]
            else:
                rm_name_ = None#self._extract_room_name(data['entity_id']).split(' ')[1]
            if action == 'turn_on':
                self.signal.http_error.emit(f"Can't connect to device from ROOM {rm_name_}.\nHTTP error: {e}")
            else:
                self.signal.http_error.emit(f"Manually turn off the breaker on ROOM {rm_name_}.\nHTTP error: {e}")
            return [response.status_code, rm_name_]

    def get_devices(self):
        """Fetch devices and update the state summary."""
        try:
            devices_data, rm_name = self._request('GET', '/api/states')
            #print (devices_data, '<----- devices_data')
            if devices_data:
                self.devices = devices_data
                #print (self.devices, '<----- devices')
                self.switch_state_summary = self._summarize_switches(devices_data)
                #print (self.switch_state_summary, '<----- switch_state_summary')
                self.active_rooms = self._update_active_rooms(self.switch_state_summary)
                #print (self.active_rooms)
                self.signal.update_active_rooms.emit(self.active_rooms)
            else:
                print("Failed to fetch devices or no devices found.")
        except Exception as e:
            print(f"An error occurred while fetching devices: {e}")

    def _summarize_switches(self, devices):
        """Summarize switches based on their states."""
        summary = {}
        for device in devices:
            #print (device)
            friendly_name = device['attributes'].get('friendly_name', '')
            #print (friendly_name, '<----- friendly_name')
            #check if friendly name is a number
            if friendly_name.isdigit():

                state = device['state']
                #print (state, '<----- state')
                if state not in summary:
                    summary[state] = []
                summary[state].append(friendly_name)
        return summary

    def _update_active_rooms(self, switch_state_summary):
        """Update active rooms based on the state of switches."""
        active_rooms = []
        for state, friendly_names in switch_state_summary.items():
            for friendly_name in friendly_names:
                room_number = re.findall(r'\d+', friendly_name)
                room_name = f"Room {int(room_number[0])}" if room_number else "Unknown Room"
                active_rooms.append([room_name, state.upper()])
            
        return active_rooms

    def _control_device(self, action, entity_id):
        """Helper method to turn a device on or off."""
        if entity_id:
            endpoint = f"/api/services/switch/{action}"
            data = {"entity_id": entity_id}
            room_name = self._extract_room_name(entity_id)

            response, rm_name_ = self._request('POST', endpoint, data, action)
            #print (response,'<----- response')
            if response == 200:
                self.signal.save_to_db.emit(rm_name_)
                if room_name in self.unavailable_rooms:
                    self.unavailable_rooms.remove(room_name)
                self.get_devices()
                return True
            else:
                if room_name not in self.unavailable_rooms:
                    self.unavailable_rooms.append(room_name)
                self.signal.update_inactive_rooms.emit(self.unavailable_rooms)
                return False
        else:
            #print(f"Error: Device with entity_id '{entity_id}' not found.")
            return False

    def _extract_room_name(self, entity_id):
        """Extract room name from entity_id."""
        number = re.findall(r'\d+', entity_id)
        return f"Room {number[0]}" if number else "Unknown Room"

    def turn_on_device(self, entity_id):
        """Turn on a device."""
        return self._control_device('turn_on', entity_id)

    def turn_off_device(self, entity_id):
        """Turn off a device."""
        return self._control_device('turn_off', entity_id)

    def threaded_device_control(self, func, entity_id):
        """Run device control in a separate thread."""
        thread = threading.Thread(target=func, args=(entity_id,))
        thread.start()
        return thread

    def run(self):
        """Run the task periodically every 10 seconds."""
        #print ('run')
        while self.running:
            #print ('running')
            start_time = time.time()  # Get the current time
            #print (start_time, '<----- start_time')
            self.get_devices()  # Perform the task

            elapsed_time = time.time() - start_time
            sleep_time = max(10 - elapsed_time, 0)  # Ensure we don't sleep negative time
            time.sleep(sleep_time)  # Sleep for the remaining time to complete the 10-second interval



    def start_monitoring(self):
        """Start monitoring the devices in a separate thread."""
        #print ('start monitoring')
        monitoring_thread = threading.Thread(target=self.run)
        monitoring_thread.start()
        return monitoring_thread

    def stop_monitoring(self):
        """Stop monitoring."""
        self.running = False


if __name__ == "__main__":
    snapshot = 'Resource/config.json'
    with open(snapshot, 'r') as file:
        config_data = json.load(file)
    
    hass_api = config_data['HASS_API']
    #print (hass_api, '<----- hass_api')
    HOME_ASSISTANT_URL = "http://homeassistant.local:8123"
    API_TOKEN = hass_api

    ha_summary = HomeAssistantSwitchSummary(HOME_ASSISTANT_URL, API_TOKEN)
    monitoring_thread = ha_summary.start_monitoring()

    # Example usage to turn on and off devices in separate threads by friendly_name
    ha_summary.threaded_device_control(ha_summary.turn_on_device, 'switch.1')
    # ha_summary.threaded_device_control(ha_summary.turn_off_device, 'switch.2_switch')
