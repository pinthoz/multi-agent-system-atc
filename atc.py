# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import math
from geopy.distance import geodesic
import random
import re




class Environment:
    def __init__(self): 
        # Initialize environment variables, e.g., aircraft positions, weather, runways, etc.
        self.aircraft_positions = {100 : (41.23556,-8.67806,0), 200 : (42.00000,-8.00000,0)} # {aircraft_id: position-> (x, y, z)}
        self.weather_conditions = {} # {weather_data}
        self.runway_status = {1 : 1, 2 : 1, 3 : 1, 4:0 , 5: 1, 6:1} # {runway_id: status -> 0/1}
        self.aeroports = {1 : (42.00000,-8.00000,0), 2 : (42.00000,-8.00000,0), 3 : (41.23556,-8.67806,0), 4 : (41.23556,-8.67806,0), 5 : (39.50000, -8.00000, 0) , 6: (38.77944,-9.13611,0)} # {runway_id: position-> (x, y, z)}
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



class AirTrafficControlAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment


    async def setup(self):
        # Define a behavior to perceive and interact with the environment
        class EnvironmentInteraction(CyclicBehaviour):
            async def run(self):

                weather_data = self.get_weather_data()

            def get_aircraft_position(self):
                # Retrieve aircraft position from the environment
                position = self.agent.environment.get_aircraft_position(100)
                return position

            def get_weather_data(self):
                # Retrieve weather data from the environment
                weather_data = self.agent.environment.get_weather_data()
                return weather_data
            

        # Add the behavior to the agent
        class MessageHandling(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg:
                    if msg.body.startswith("Warning"):
                        print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}.\nI will be attentive to any problems that may occur\n")
                    else:
                        position_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                        aircraft_id = int(re.search(r'\d+', msg.body).group())
                        if position_match:
                            x, y, z = map(float, position_match.groups())
                            self.agent.environment.aircraft_positions[aircraft_id] = (x, y, z)
                        print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")
                        # Handle the message here, e.g., provide instructions to the aircraft
        

        # Add the behaviors to the agent
        self.add_behaviour(EnvironmentInteraction())
        self.add_behaviour(MessageHandling())
    

class RunwayManagerAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment

    
    async def setup(self):
        class RunwayAvailable(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg:
                    if msg.metadata["performative"] == "propose":
                        # Handle the runway request message
                        print(f"Received runway request: {msg.body} from {msg.sender}")    
                        coordinates_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                        coordinates = tuple(map(float, coordinates_match.groups()))
                        requested_runway_id = self.agent.environment.get_runway_id(coordinates)
                        runway_is_available = self.get_runway_status(requested_runway_id)
                        if runway_is_available == 1:
                            # Create an ACL message to send data to the air traffic control agent
                            airport_id = self.agent.environment.get_airport_id(requested_runway_id)  # Assuming a method to get the airport ID
                            msg = Message(to=str(msg.sender))
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {requested_runway_id} at Airport {airport_id} is available."
                            # Send the message
                            await self.send(msg)
                        else:
                            msg = Message(to=str(msg.sender))
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {requested_runway_id} is not available."
                            # Send the message
                            await self.send(msg)

            def get_runway_status(self, runway_id):
                # Retrieve runway status from the environment
                status = self.agent.environment.get_runway_status(runway_id)
                return status

                    
        
        self.add_behaviour(RunwayAvailable())
        


class AircraftAgent(Agent):
    def __init__(self, jid, password, environment, aircraft_id, runway_id):
        super().__init__(jid, password)
        self.environment = environment
        self.aircraft_id = aircraft_id
        self.runway_id = runway_id
        self.reached_destination = False
        self.new_route_event = asyncio.Event()
        self.change_route = False
        self.aircraft_position = self.environment.get_aircraft_position(self.aircraft_id)
        self.destination = self.environment.get_airport_coord(self.runway_id)
        
    async def setup(self):
        # Define a behavior to interact with the environment and air traffic control
        class AircraftInteraction(CyclicBehaviour):
            async def run(self):
                await asyncio.sleep(2)
                distance_to_other_aircraft = 1000000

                for other_aircraft_id in self.agent.environment.aircraft_positions:
                    if other_aircraft_id != self.agent.aircraft_id:
                        other_aircraft_position = self.agent.environment.get_aircraft_position(other_aircraft_id)
                        distance_to_other_aircraft = geodesic(
                            (self.agent.aircraft_position[0], self.agent.aircraft_position[1]),
                            (other_aircraft_position[0], other_aircraft_position[1])
                        ).kilometers
                        print("distance_to_other_aircraft: ", distance_to_other_aircraft)

                        if distance_to_other_aircraft < 50:  # Defina um limite de proximidade adequado
                            print(f"Aircraft {self.agent.aircraft_id} is too close to Aircraft {other_aircraft_id}. Performing avoidance maneuver.")
                            new_position = self.perform_avoidance_manoeuver(self.agent.aircraft_position, other_aircraft_position)
                            new_position_with_altitude = (new_position[0], new_position[1], new_position[2]- 500)
                            self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position_with_altitude)
                            self.agent.change_route = True  # Informar ao agente de aeronave para gerar uma nova rota
                
                if self.agent.change_route:
                    msg = Message(to="atc_agent@localhost")
                    msg.set_metadata("performative", "informe")
                    msg.body = f"Warning! Aircraft {self.agent.aircraft_id} is too close to another aircraft. Performing avoidance maneuver."
                    self.agent.change_route = False
                    await self.send(msg)
                            


            def perform_avoidance_manoeuver(self, current_position, other_aircraft_position):
                # Realizar a manobra de desvio para aumentar a distância
                avoidance_strength = 1.2 # Ajuste conforme necessário para controlar a intensidade da manobra
                angle = math.atan2(other_aircraft_position[1] - current_position[1],
                                other_aircraft_position[0] - current_position[0])
                avoidance_vector = (
                    avoidance_strength * math.cos(angle),
                    avoidance_strength * math.sin(angle)
                )

                new_position = (
                    current_position[0] + avoidance_vector[0],
                    current_position[1] + avoidance_vector[1],
                    current_position[2]  # Supondo que a altitude permanece a mesma
                )

                return new_position



        class AircraftInteractionRunway(CyclicBehaviour):
            async def run(self):
                await asyncio.sleep(2)
                #print("AircraftInteraction behavior is running")
                # Perceive environment data
                self.agent.aircraft_position = self.get_aircraft_position(self.agent.aircraft_id)
                
                new_position = self.move_towards(self.agent.aircraft_position, self.agent.destination, 1000000, 100)
                
                distance_to_destination = geodesic((new_position[0], new_position[1]), (self.agent.destination[0], self.agent.destination[1])).meters
                
                
                if distance_to_destination <= 3000 :
                    #request runway availability
                    if not self.agent.reached_destination:
                        msg = Message(to="runway_agent@localhost")
                        msg.set_metadata("performative", "propose")
                        msg.body = f"Some runway available for aeroport {self.agent.destination}?"
                        
                        await self.send(msg)
                    
                    
                if not self.agent.reached_destination:

                    self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position)  

                    await self.send_instruction_to_atc(self.agent.aircraft_position, distance_to_destination)
                else:
                    await self.land_aircraft()
                    new_position
                    print(self.agent.environment.runway_status)
                    await self.send_instruction_to_atc(self.agent.aircraft_position, 0)

                    await self.agent.new_route_event.wait()


                    self.agent.new_route_event.clear()
                

                    

            def get_aircraft_position(self, aircraft_id):
                # Access the environment object to retrieve the aircraft's position
                return self.agent.environment.get_aircraft_position(aircraft_id)
            
            def move_towards(self, current_position, destination_position, velocity, dt):
                """Move towards the destination position with a given velocity."""
                current_coord = (current_position[0], current_position[1])
                destination_coord = (destination_position[0], destination_position[1])


                distance = geodesic(current_coord, destination_coord).meters


                if distance == 0:
                    return destination_position


                time_to_destination = distance / velocity

                ratio = 1.0 / (time_to_destination * dt)
                new_position = (
                    current_position[0] + ratio * (destination_position[0] - current_position[0]),
                    current_position[1] + ratio * (destination_position[1] - current_position[1]),
                    9000 
                )

                return new_position
            

            async def send_instruction_to_atc(self, position,distance):
                # Create an ACL message to send data to the air traffic control agent   
                msg = Message(to="atc_agent@localhost")  # Replace with the correct ATC agent JID
                msg.set_metadata("performative", "inform")
                msg.body = f"Aircraft {self.agent.aircraft_id} at position {position} requesting instructions.\nDistance to destination: {round(distance)} meters."
                
                if self.agent.reached_destination:
                    new_position = (position[0], position[1], 0)
                    msg.body = f"Aircraft {self.agent.aircraft_id} reached destination at runway {self.agent.runway_id} in {new_position}"


                # Send the message
                await self.send(msg)
            
            async def land_aircraft(self):
                # Update the runway status in the environment (mark it as not available)
                self.agent.environment.update_runway_status(self.agent.runway_id, 0)

        class AnyProblem(CyclicBehaviour):
            haveProblem = random.randint(0, 5)
            if haveProblem == 5:
                async def run(self):
                    #print("Aircraft have a problem")
                    # Create an ACL message to send data to the air traffic control agent   
                    pass
                
                
        class MessageHandling(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg:
                    if "is available" in msg.body:

                        runway_id = int(re.search(r'\d+', msg.body).group())
                        self.agent.runway_id = runway_id
                        self.agent.reached_destination = True
                        
                    elif "new route started" in msg.body:

                        self.agent.new_route_event.set()

                    print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")

        # Add the behavior to the agent
        self.add_behaviour(AircraftInteractionRunway())
        self.add_behaviour(MessageHandling())
        self.add_behaviour(AircraftInteraction())
        #self.add_behaviour(AnyProblem())

        

async def main():
    # Create and initialize the environment
    atc_environment = Environment()
    
    atc_agent = AirTrafficControlAgent("atc_agent@localhost", "1234", atc_environment)
    
    aircraft_agent1 = AircraftAgent("aircraft_agent1@localhost", "1234", atc_environment, 100, 1)
    aircraft_agent2 = AircraftAgent("aircraft_agent2@localhost", "1234", atc_environment, 200, 3)
    runway_agent = RunwayManagerAgent("runway_agent@localhost", "1234", atc_environment)

    await atc_agent.start()
    await aircraft_agent2.start()
    await aircraft_agent1.start()
    await runway_agent.start()



if __name__ == "__main__":
    spade.run(main())


