from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import asyncio
from geopy.distance import geodesic
import random
import math
import re
from airportDatabase import AirportDatabase


class AircraftAgent(Agent):
    def __init__(self, jid, password, environment, aircraft_id, runway_id):
        super().__init__(jid, password)
        self.environment = environment
        self.aircraft_id = aircraft_id
        self.runway_id = runway_id
        self.reached_destination = False
        self.change_route = False
        self.aircraft_position = self.environment.get_aircraft_position(self.aircraft_id)
        self.destination = self.environment.get_airport_coord(self.runway_id)
        self.landed = False
        self.problem = False
        self.distance_travelled = 0
        self.request_land = False

        
    async def setup(self):
        # Define a behavior to interact with the environment and air traffic control
        
        class AircraftInteraction(CyclicBehaviour):
            async def run(self):
                
                if not self.agent.landed:
                    #await self.agent.new_route_event.wait()
                
                    await asyncio.sleep(2)
                    distance_to_other_aircraft = 1000000

                    for other_aircraft_id in self.agent.environment.aircraft_positions:
                        if other_aircraft_id != self.agent.aircraft_id:
                            other_aircraft_position = self.agent.environment.get_aircraft_position(other_aircraft_id)
                            distance_to_other_aircraft = geodesic(
                                (self.agent.aircraft_position[0], self.agent.aircraft_position[1]),
                                (other_aircraft_position[0], other_aircraft_position[1])
                            ).kilometers
                            #print("distance_to_other_aircraft: ", distance_to_other_aircraft)

                            if distance_to_other_aircraft < 50 and other_aircraft_position[2] != 0:  # Defina um limite de proximidade adequado
                                print(f"Aircraft {self.agent.aircraft_id} is too close to Aircraft {other_aircraft_id}. Performing avoidance maneuver.")
                                new_position = self.perform_avoidance_manoeuver(self.agent.aircraft_position, other_aircraft_position)
                                new_position_with_altitude = (new_position[0], new_position[1], new_position[2]- 500)
                                self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position_with_altitude)
                                self.agent.change_route = True  # Informar ao agente de aeronave para gerar uma nova rota


                    if self.agent.change_route:
                        msg = Message(to="atc_agent@localhost")
                        msg.set_metadata("performative", "inform")
                        msg.body = f"Warning! Aircraft {self.agent.aircraft_id} is too close to another aircraft. Performing avoidance maneuver."
                        self.agent.change_route = False
                        await self.send(msg)

                else:
                    self.agent.environment.update_aircraft_position(self.agent.aircraft_id, self.agent.destination)
                    airport_db = AirportDatabase()
                    old_runway = self.agent.runway_id
                    index = random.randint(0, 4)
                    new_airport = airport_db.get_coor(index)
                    print('-----------------------------------')
                    print("NEW AIRPORT " +  str(new_airport))
                    print('-----------------------------------')
                    runway = self.agent.environment.get_new_runway(new_airport)
                    print (runway)
                    print('-----------------------------------')
                    self.agent.runway_id = runway
                    self.agent.destination = new_airport
                    self.agent.landed = False
                    self.agent.distance_travelled = 0
                    
                    for other_aircraft_id in self.agent.environment.aircraft_positions:
                        if other_aircraft_id != self.agent.aircraft_id:
                            msg = Message(to=f"aircraft_agent{str(other_aircraft_id)[0]}@localhost")  # Replace with the correct aircraft agent JID
                            msg.set_metadata("performative", "query")
                            msg.body = f"Query: Are you heading to the destination {self.agent.destination}?"
                            msg.set_metadata("reply-to", str(self.agent.jid))  # Configura o campo "reply-to" com o JID do remetente (AircraftAgent)
                            await self.send(msg)
                            self.agent.environment.update_request_coord(self.agent.aircraft_id)
                            
                            response = await self.receive(timeout=10) 
                            if response and "aircraft_agent" in str(response.sender) and response.metadata["performative"] == "inform":
                                print("-----------------------------------")
                                print(f"Aircraft {self.agent.aircraft_id} received a response from {response.sender}: {response.body}")
                                if str(response.body) == "Yes":
                                    print("Waiting...")
                                    await asyncio.sleep(5)
                                    print("End of waiting...")

                            
                    await asyncio.sleep(5)
                        
                    print(f"{new_airport} + {airport_db.get_name(new_airport)}")
                    self.agent.environment.update_runway_status(old_runway, 1)
                    



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
                
                if not self.agent.landed:
                    #await self.agent.new_route_event.wait()
                    
                    await asyncio.sleep(2)
                    #print(self.agent.problem)
                    #print("AircraftInteraction behavior is running")
                    # Perceive environment data
                    self.agent.aircraft_position = self.get_aircraft_position(self.agent.aircraft_id)
                    
                    new_position = self.move_towards(self.agent.aircraft_position, self.agent.destination, 1000000, 100)
                    
                    distance_to_destination = geodesic((new_position[0], new_position[1]), (self.agent.destination[0], self.agent.destination[1])).meters
                    
                    airport_db = AirportDatabase()
                    
                    airport_name = airport_db.get_name(self.agent.destination)
                    
                    if distance_to_destination <= 6000 :
                        #request runway availability
                        if not self.agent.reached_destination:
                            
                            if self.agent.environment.get_weather_data(self.agent.destination) == "bad":
                                new_destination = self.agent.environment.find_closest_airport(self.agent.destination)
                                msg = Message(to="runway_agent@localhost")
                                msg.set_metadata("performative", "propose")
                                msg.body = f"Some runway available for aeroport {airport_db.get_name(new_destination)} : {new_destination}?"
                                await self.send(msg)
                                self.agent.destination = new_destination
                            else:
                                msg = Message(to="runway_agent@localhost")
                                msg.set_metadata("performative", "propose")
                                msg.body = f"Some runway available for aeroport {airport_name} : {self.agent.destination}?"
                                
                                await self.send(msg)
                            
                            
                        
                    if not self.agent.reached_destination:

                        self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position)  

                        await self.send_instruction_to_atc(self.agent.aircraft_position, distance_to_destination)
                    else:
                        
                        await self.land_aircraft()
                        print(self.agent.environment.runway_status)
                        await self.send_instruction_to_atc(self.agent.aircraft_position, 0)

                        self.agent.landed = True   
                

                    

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
                
                self.agent.distance_travelled += geodesic((current_position[0], current_position[1]), (new_position[0], new_position[1])).meters
                print(f"Distance travelled by aircraft {self.agent.aircraft_id}: {round(self.agent.distance_travelled)} meters.")
                return new_position
            

            async def send_instruction_to_atc(self, position,distance):
                # Create an ACL message to send data to the air traffic control agent
                
                msg = Message(to="atc_agent@localhost")  # Replace with the correct ATC agent JID
                msg.set_metadata("performative", "inform")
                msg.body = f"Aircraft {self.agent.aircraft_id} at position {position} requesting instructions.\nDistance to destination: {round(distance)} meters."
                
                airport_db = AirportDatabase()
                airport_name = airport_db.get_name(self.agent.destination)
                if self.agent.reached_destination:
                    new_position = (position[0], position[1], 0)
                    msg.body = f"Aircraft {self.agent.aircraft_id} reached destination at runway {self.agent.runway_id} in {new_position} at {airport_name}."


                # Send the message
                await self.send(msg)
            
            async def land_aircraft(self):
                # Update the runway status in the environment (mark it as not available)
                self.agent.environment.update_runway_status(self.agent.runway_id, 0)

        class AnyProblem(CyclicBehaviour):
            async def run(self):
                if not self.agent.landed:
                    await asyncio.sleep(3)
                    have_problem = random.randint(0, 25)
                    if have_problem == 5:
                        #print("Aircraft have a problem")
                        # Create an ACL message to send data to the air traffic control agent   
                        self.agent.problem = True

                
                
        class MessageHandling(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg:
                    if "is available" in msg.body:
                        runway_id = int(re.search(r'\d+', msg.body).group())
                        self.agent.runway_id = runway_id
                        self.agent.reached_destination = True
                        
                    #print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")
                    
        class SendMessageAirport(CyclicBehaviour):
            async def run(self):
                if (self.agent.environment.has_1_value(self.agent.environment.request_coord)):
                    msg = await self.receive(timeout=10)
                    if msg and "aircraft_agent" in str(msg.sender) and msg.metadata["performative"] == "query":
                        print(f"Recebeu mensagem de {msg.sender} com conteudo {msg.body}")

                        # Envia uma resposta ao remetente original usando o JID do campo "reply-to"
                        response = Message(to=msg.metadata["reply-to"])
                        response.set_metadata("performative", "inform")
                        cord = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', str(msg.body))
                        if (self.agent.destination == (float(cord.group(1)), float(cord.group(2)), int(cord.group(3)))): 
                            response.body = "Yes"
                        else:
                            response.body = "No"
                        await self.send(response)
                        
                        print(f"Aircraft {self.agent.aircraft_id} sent a response to {msg.sender}: {response.body}")
                    self.agent.environment.update_all_request_coord_to_0()
                    
        
        class Emergency(CyclicBehaviour):
            async def run(self):
                if self.agent.problem:
                    airport_db = AirportDatabase()
                    request_airport = Message(to=f"atc_agent@localhost")
                    request_airport.set_metadata("performative", "request")
                    request_airport.body = "Emergency! Find me the closest airport"
                    await self.send(request_airport) 
                    airport_request= await self.receive(timeout=10)
                    if airport_request and airport_request.metadata["performative"] == "inform":
                        print(f"Recebeu mensagem de {airport_request.sender} com conteudo {airport_request.body}")
                        cord = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', str(airport_request.body))
                        closest_airport = (float(cord.group(1)), float(cord.group(2)), int(cord.group(3)))
                    
                        for other_aircraft_id in self.agent.environment.aircraft_positions:
                            if other_aircraft_id != self.agent.aircraft_id:
                                request = Message(to=f"aircraft_agent{str(other_aircraft_id)[0]}@localhost")
                                request.set_metadata("performative", "emergency")
                                #closest_airport = self.agent.environment.find_closest_airport(self.agent.aircraft_position)
                                request.body = f"Emergency: I need to land in {airport_db.get_name(closest_airport)} : {closest_airport}! Please, let me land!"
                                print(f"I need to land in {airport_db.get_name(closest_airport)} : {closest_airport}")
                                await self.send(request)
                                
                        self.agent.request_land = True
                        self.agent.destination = closest_airport
                        self.agent.problem = False
                    
        class Emergency_Airport(CyclicBehaviour):
            async def run(self):
                if self.agent.request_land:
                    msg = await self.receive(timeout=10)
                    if msg and "aircraft_agent" in str(msg.sender) and msg.metadata["performative"] == "emergency":
                        print(f"Recebeu mensagem de {msg.sender} com conteudo {msg.body}")

                        # Envia uma resposta ao remetente original usando o JID do campo "reply-to"
                        response = Message(to=msg.metadata["reply-to"])
                        response.set_metadata("performative", "inform")
                        cord = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', str(msg.body))
                        if (self.agent.destination == (float(cord.group(1)), float(cord.group(2)), int(cord.group(3)))): 
                            response.body = "I wait for you"
                            #lógica para ele esperar o outro avião pousar
                        else:
                            response.body = "No"
                        await self.send(response)
                        
                        print(f"Aircraft {self.agent.aircraft_id} sent a response to {msg.sender}: {response.body}")
                    self.agent.request_land = False
                    
        class ReceiveEmergencyMessage(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg and msg.body.startswith("Emergency: I need to land"):
                    print(f"{str(msg.to)} i receive your message")
                    


                    
        # Add the behavior to the agent
        self.add_behaviour(AircraftInteractionRunway())
        self.add_behaviour(MessageHandling())
        self.add_behaviour(AircraftInteraction())
        self.add_behaviour(AnyProblem())
        self.add_behaviour(SendMessageAirport())
        self.add_behaviour(Emergency())
        self.add_behaviour(Emergency_Airport())
        self.add_behaviour(ReceiveEmergencyMessage())