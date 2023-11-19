import random
from geopy.distance import geodesic

class Environment:
    def __init__(self): 
        # Initialize environment variables, e.g., aircraft positions, weather, runways, etc.
        self.aircraft_positions = {100 : (41.23697, -8.67069,0), 200 : (41.72512, -7.46632,0) , 300 : (39.84483, -7.44015, 0), 400: (38.78003, -9.13495,0)} # {aircraft_id: position-> (x, y, z)}
        self.weather_conditions = {
            (41.72512, -7.46632): "good",
            (41.23697, -8.67069): "good",
            (39.84483, -7.44015): "good",
            (38.78003, -9.13495): "good",
            (37.02036, -7.96829): "good"
        } # {weather_data}
        self.runways_in_airports = {(41.72512,-7.46632,0): [1,2], (41.23697,-8.67069,0): [3,4], (39.84483,-7.44015, 0): [5], (38.78003, -9.13495,0): [6], (37.02036,-7.96829,0): [7]}
        self.runway_status = {1 : 1, 2 : 0, 3 : 1, 4:1 , 5: 1, 6:1, 7:0} # {runway_id: status -> 0/1}
        self.aeroports = {1 : (41.72512, -7.46632,0), 2 : (41.72512, -7.46632,0), 3 : (41.23697, -8.67069,0), 4 : (41.23697, -8.67069,0), 5 : (39.84483, -7.44015, 0) , 6: (38.78003, -9.13495,0), 7:(37.02036, -7.96829)} # {runway_id: position-> (x, y, z)}
        
        self.request_coord = {100 : 0, 200 : 0 , 300 : 0, 400: 0}
        
    def update_aircraft_position(self, aircraft_id, position):
        self.aircraft_positions[aircraft_id] = position
        #print(f"Aircraft {aircraft_id} is at position {position}")

    def update_weather(self, weather_data, coord):
        self.weather_conditions[coord] = weather_data
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

    def get_new_runway(self, airport):
        runway_ids = self.runways_in_airports[airport]
        if runway_ids:
            return random.choice(runway_ids)
        
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
    
    def update_request_coord(self, aircraft_id):
        self.request_coord[aircraft_id] = 1
        
        
    def has_1_value(self, request):
        return any(value == 1 for value in request.values())
    
    def update_all_request_coord_to_0(self):
        for aircraft_id in self.request_coord:
            self.request_coord[aircraft_id] = 0

    def find_closest_airport(self, current_position):

        closest_airport_id = None
        min_distance = float('inf')

        for airport_position, runway in self.runways_in_airports.items():
            distance = geodesic(current_position[:2], airport_position[:2]).meters

            if distance < min_distance:
                min_distance = distance
                closest_airport_id = airport_position

        return closest_airport_id