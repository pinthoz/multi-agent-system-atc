import random
<<<<<<< Updated upstream
=======
from geopy.distance import geodesic
from airportDatabase import AirportDatabase
>>>>>>> Stashed changes

class Environment:
    '''
    O ambiente é composto por:
    - As posições dos aviões
    - As condições meteorológicas em cada aeroporto
    - As pistas de aterragem de cada aeroporto
    '''
    def __init__(self): 
        
        self.aircraft_positions = {100 : (41.23697, -8.67069,0), 200 : (41.72512, -7.46632,0) , 300 : (39.84483, -7.44015, 0), 400: (38.78003, -9.13495,0), 500: (37.02036, -7.96829, 0), 600: (38.78003, -9.13495,0)} # {aircraft_id: position-> (x, y, z)}
        self.weather_conditions = {
<<<<<<< Updated upstream
            (41.72512, -7.46632): "good",
            (41.23697, -8.67069): "good",
            (39.84483, -7.44015): "good",
            (38.78003, -9.13495): "good",
            (37.02036, -7.96829): "good"
        } # {weather_data}
        self.runways_in_airports = {(41.72512,-7.46632,0): [1,2], (41.23697,-8.67069,0): [3,4], (39.84483,-7.44015, 0): [5], (38.78003, -9.13495,0): [6], (37.02036,-7.96829,0): [7]}
        self.runway_status = {1 : 1, 2 : 0, 3 : 1, 4:1 , 5: 1, 6:1, 7:0} # {runway_id: status -> 0/1}
        self.aeroports = {1 : (41.72512, -7.46632,0), 2 : (41.72512, -7.46632,0), 3 : (41.23697, -8.67069,0), 4 : (41.23697, -8.67069,0), 5 : (39.84483, -7.44015, 0) , 6: (38.78003, -9.13495,0), 7:(37.02036, -7.96829)} # {runway_id: position-> (x, y, z)}
=======
            (41.72512, -7.46632, 0): "good",
            (41.23697, -8.67069, 0): "good",
            (39.84483, -7.44015, 0): "good",
            (38.78003, -9.13495, 0): "good",
            (37.02036, -7.96829, 0): "good"
        } 
        self.runways_in_airports = {(41.72512,-7.46632,0): [1], (41.23697,-8.67069,0): [2,3], (39.84483,-7.44015, 0): [4], (38.78003, -9.13495,0): [5,6], (37.02036,-7.96829,0): [7]}
        self.runway_status = {1 : 1, 2 : 1, 3 : 1, 4:1 , 5: 1, 6:1, 7:1} # {runway_id: status -> 0/1}
        self.aeroports = {1 : (41.72512, -7.46632,0), 2 : (41.23697,-8.67069,0), 3 : (41.23697, -8.67069,0), 4 : (39.84483,-7.44015, 0), 5 : (38.78003, -9.13495,0) , 6: (38.78003, -9.13495,0), 7:(37.02036, -7.96829, 0)} # {runway_id: position-> (x, y, z)}
>>>>>>> Stashed changes
        
        self.request_coord = {100 : 0, 200 : 0 , 300 : 0, 400: 0, 500:0, 600:0}
        
        self.priority_queue = {(41.72512, -7.46632, 0): [],
                               (41.23697, -8.67069, 0): [],
                               (39.84483, -7.44015, 0): [],
                               (38.78003, -9.13495, 0): [],
                               (37.02036, -7.96829, 0): []
                              }  
        
    def update_aircraft_position(self, aircraft_id, position):
        # Atualiza a posição do avião
        self.aircraft_positions[aircraft_id] = position

    def update_weather(self, weather_data, coord):
        airport_db = AirportDatabase()
        # Atualiza as condições meteorológicas
        self.weather_conditions[coord] = weather_data
        print(f"Weather conditions updated: {weather_data} at {airport_db.get_name(coord)}")

    def update_runway_status(self, runway_id, status):
        # Atualiza o estado da pista
        self.runway_status[runway_id] = status
        print(f"Runway {runway_id} status updated to {status}")

    def get_aircraft_position(self, aircraft_id):
        # Retorna a posição do avião
        if aircraft_id in self.aircraft_positions:
            return self.aircraft_positions[aircraft_id]
        else:
            print(f"Aircraft {aircraft_id} not found.")
            return None

<<<<<<< Updated upstream
    def get_weather_data(self):
        return self.weather_conditions
=======
    def get_weather_data(self, airport):
        # Retorna as condições meteorológicas no aeroporto
        return self.weather_conditions[airport]
>>>>>>> Stashed changes

    def get_runway_status(self, runway_id):
        # Retorna o estado da pista
        if runway_id in self.runway_status:
            print(f"Runway {runway_id} status: {self.runway_status[runway_id]}")
            return self.runway_status[runway_id]
        else:
            print(f"Runway {runway_id} not found.")
            return None
    
    def get_runway_id(self, airport):
        # Retorna uma pista disponível no aeroporto
        runway_ids = [runway_id for runway_id, status in self.runway_status.items() if status == 1 and self.aeroports[runway_id] == airport]
        if runway_ids:
            return random.choice(runway_ids)
        else:
            print("No runway available.")
            return None

    def get_new_runway(self, airport):
        # Retorna uma pista no aeroporto
        runway_ids = self.runways_in_airports[airport]
        if runway_ids:
            return random.choice(runway_ids)
        
    def get_airport_coord(self,runway_id):
        # Retorna as coordenadas do aeroporto
        if runway_id in self.aeroports:
            return self.aeroports[runway_id]
        else:
            print(f"Runway {runway_id} not found.")
            return None
        
    def get_airport_id(self, runway_id):
        # Retorna o id do aeroporto a partir do id da pista
        id_a = None
        for airport_id, airport_position in self.aeroports.items():
            if airport_id == runway_id:
                id_a = airport_position
        if id_a != None:
            return id_a
        return
    
    
    
    
    def update_request_coord(self, aircraft_id):
        # Atualiza o pedido de aterragem do avião
        self.request_coord[aircraft_id] = 1
        
        
    def has_1_value(self, request):
        # Verifica se algum dos aviões pediu aterragem
        return any(value == 1 for value in request.values())
    
    def update_all_request_coord_to_0(self):
        # Atualiza todos os pedidos de aterragem para 0
        for aircraft_id in self.request_coord:
            self.request_coord[aircraft_id] = 0
<<<<<<< Updated upstream
=======

    def find_closest_airport(self, current_position):
        # Retorna o aeroporto mais próximo do avião ou do aeroporto
        closest_airport_id = None
        min_distance = float('inf')

        for airport_position, runway in self.runways_in_airports.items():
            distance = geodesic(current_position[:2], airport_position[:2]).meters

            if distance < min_distance and distance> 0:
                min_distance = distance
                closest_airport_id = airport_position

        return closest_airport_id
>>>>>>> Stashed changes
