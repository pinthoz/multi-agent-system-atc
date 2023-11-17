import random

class Environment:
    def __init__(self): 
        # Initialize environment variables, e.g., aircraft positions, weather, runways, etc.
        self.aircraft_positions = {100 : (41.23697, -8.67069,0), 200 : (41.72512, -7.46632,0)} # {aircraft_id: position-> (x, y, z)}
        self.weather_conditions = {} # {weather_data}
        self.runway_status = {1 : 1, 2 : 0, 3 : 1, 4:0 , 5: 1, 6:1} # {runway_id: status -> 0/1}
        self.aeroports = {1 : (41.72512, -7.46632,0), 2 : (41.72512, -7.46632,0), 3 : (41.23697, -8.67069,0), 4 : (41.23697, -8.67069,0), 5 : (39.84483, -7.44015, 0) , 6: (38.78003, -9.13495,0), 7:(37.02036, -7.96829)} # {runway_id: position-> (x, y, z)}
        #usar sempre 5 casa decimais para funcionar com o pedido de runway
        
    def update_aircraft_position(self, aircraft_id, position):
        self.aircraft_positions[aircraft_id] = position
        print(f"Aircraft {aircraft_id} is at position {position}")

    def update_weather(self, weather_data):
        self.weather_conditions = weather_data
        print("Weather conditions updated:", weather_data)

    def update_runway_status(self, runway_id, status):
        self.runway_status[runway_id] = status
        print(f"Runway {runway_id} status updated to {status}")

    def get_aircraft_position(self, aircraft_id):
        if aircraft_id in self.aircraft_positions:
            return self.aircraft_positions[aircraft_id]
        else:
            print(f"Aircraft {aircraft_id} not found.")
            return None

    def get_weather_data(self):
        return self.weather_conditions

    def get_runway_status(self, runway_id):
        if runway_id in self.runway_status:
            print(f"Runway {runway_id} status: {self.runway_status[runway_id]}")
            return self.runway_status[runway_id]
        else:
            print(f"Runway {runway_id} not found.")
            return None
    
    def get_runway_id(self, airport):
        # Retrieve one of runway id from the environment with status 1
        runway_ids = [runway_id for runway_id, status in self.runway_status.items() if status == 1 and self.aeroports[runway_id] == airport]
        if runway_ids:
            return random.choice(runway_ids)
        else:
            print("No runway available.")
            return None
        
    def get_airport_coord(self,runway_id):
        if runway_id in self.aeroports:
            return self.aeroports[runway_id]
        else:
            print(f"Runway {runway_id} not found.")
            return None
        
    def get_airport_id(self, runway_id):
        id_a = None
        for airport_id, airport_position in self.aeroports.items():
            if airport_id == runway_id:
                id_a = airport_position
        if id_a != None:
            return id_a
        return