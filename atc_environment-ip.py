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
        self.aircraft_positions = {100 : (41.23556,-8.67806,0)} # {aircraft_id: position-> (x, y, z)}
        self.weather_conditions = {} # {weather_data}
        self.runway_status = {1 : 0, 2 : 1} # {runway_id: status -> 0/1}
        self.aeroports = {1 : (38.77944,-9.13611,0), 2 : (41.23556,-8.67806,0), 3 : (39.5, -8.0, 0)}

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
            return self.runway_status[runway_id]
        else:
            print(f"Runway {runway_id} not found.")
            return None
    
    def get_runway_id(self):
        # Retrieve one of runway id from the environment with status 1
        runway_ids = [runway_id for runway_id, status in self.runway_status.items() if status == 1]
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



class AirTrafficControlAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment



    async def setup(self):
        # Define a behavior to perceive and interact with the environment
        class EnvironmentInteraction(CyclicBehaviour):
            async def run(self):
                # Perceive environment data - you can use ACL messages or other means
                #aircraft_position = self.get_aircraft_position()
                weather_data = self.get_weather_data()

                # Make decisions based on perceptions and update the environment
                # Example: Check for conflicts and send instructions to aircraft

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
                    position_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                    aircraft_id = int(re.search(r'\d+', msg.body).group())
                    print("aircraft_id: ", aircraft_id)
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
        self.runway_id = self.environment.get_runway_id()
    
    async def setup(self):
        class RunwayAvailable(CyclicBehaviour):
            async def run(self):
                #print("RunwayAvailableInteraction behavior is running")
                msg = await self.receive()
                if msg:
                    if msg.metadata["performative"] == "propose":
                        # Handle the runway request message
                        print(f"Received runway request: {msg.body} from {msg.sender}")
                        runwayIsAvailable = self.get_runway_status(self.agent.environment.get_runway_id())
                        if runwayIsAvailable:
                            # Create an ACL message to send data to the air traffic control agent   
                            msg = Message(to="aircraft_agent@localhost")
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {self.agent.runway_id} is available."
                            # Send the message
                            await self.send(msg)
                        else:
                            msg = Message(to="aircraft_agent@localhost")
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {self.agent.runway_id} is not available."
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
        self.aircraft_position = self.environment.get_aircraft_position(self.aircraft_id)
        self.destination = self.environment.get_airport_coord(self.runway_id)
        
    async def setup(self):
        # Define a behavior to interact with the environment and air traffic control
        class AircraftInteraction(CyclicBehaviour):
            async def run(self):
                #print("AircraftInteraction behavior is running")
                # Perceive environment data
                self.agent.aircraft_position = self.get_aircraft_position(self.agent.aircraft_id)
                
                new_position = self.move_towards(self.agent.aircraft_position, self.agent.destination, 800, 20)
                
                distance_to_destination = geodesic((new_position[0], new_position[1]), (self.agent.destination[0], self.agent.destination[1])).meters
                
                
                if distance_to_destination <= 1000 :
                    #request runway availability
                    if not self.agent.reached_destination:
                        msg = Message(to="runway_agent@localhost")
                        msg.set_metadata("performative", "propose")
                        msg.body = f"Some runway available?"
                        
                        await self.send(msg)
                    
                    
                if not self.agent.reached_destination:
                    # Atualiza a posição da aeronave
                    self.agent.environment.update_aircraft_position(100, new_position)  
                    # Comunica com o controle de tráfego aéreo
                    await self.send_instruction_to_atc(self.agent.aircraft_position, distance_to_destination)
                else:
                    await self.land_aircraft()
                    new_position
                    print(self.agent.environment.runway_status)
                    await self.send_instruction_to_atc(self.agent.aircraft_position, 0)
                    # Aguarda o sinalizador para o início de uma nova rota
                    await self.agent.new_route_event.wait()

                    # Limpa o sinalizador para que possa ser usado novamente
                    self.agent.new_route_event.clear()
                
                

                    

            def get_aircraft_position(self, aircraft_id):
                # Access the environment object to retrieve the aircraft's position
                return self.agent.environment.get_aircraft_position(aircraft_id)
            
            def move_towards(self, current_position, destination_position, velocity, dt):
                """Move towards the destination position with a given velocity."""
                current_coord = (current_position[0], current_position[1])
                destination_coord = (destination_position[0], destination_position[1])

                # Calcula a distância usando a função geodesic do geopy
                distance = geodesic(current_coord, destination_coord).meters

                # Se a distância for zero, seta a posição para o destino
                if distance == 0:
                    return destination_position

                # Calcula o tempo necessário para percorrer a distância com a velocidade dada
                time_to_destination = distance / velocity

                # Calcula a nova posição com base no tempo e na frequência de atualização
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
                # Set the aircraft position to the ground level
                #new_position = (position[0], position[1], 0)
                #self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position)

                # Update the runway status in the environment (mark it as not available)
                self.agent.environment.update_runway_status(self.agent.runway_id, 0)

                # Notify the air traffic control about the landing
                #await self.send_instruction_to_atc(new_position, 0)  
                
                
                
        class MessageHandling(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg:
                    if "is available" in msg.body:
                        # Extrai a runway_id da mensagem e atualiza o valor no agente de aeronaves
                        runway_id = int(re.search(r'\d+', msg.body).group())
                        self.agent.runway_id = runway_id
                        self.agent.reached_destination = True
                        
                    elif "new route started" in msg.body:
                        # Sinaliza o evento de início de uma nova rota
                        self.agent.new_route_event.set()

                    print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")

        '''
        class AnyProblem(CyclicBehaviour):
            haveProblem = random.randint(0, 5)
            if haveProblem == 5:
                async def run(self):
                    #print("Aircraft have a problem")
                    # Create an ACL message to send data to the air traffic control agent   
                    msg = Message(to="atc_agent@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = f"Aircraft {self.agent.aircraft_id} have a problem."
                    # Send the message
                    await self.send(msg)
                    
    '''
        # Add the behavior to the agent
        self.add_behaviour(AircraftInteraction())
        self.add_behaviour(MessageHandling())
        #self.add_behaviour(AnyProblem())
        # continuar a implementação do comportamento de interação com o atc
        

async def main():
    # Create and initialize the environment
    atc_environment = Environment()
    
    atc_agent = AirTrafficControlAgent("atc_agent@localhost", "1234", atc_environment)
    
    aircraft_agent = AircraftAgent("aircraft_agent@localhost", "1234", atc_environment, 100, 1)
    
    runway_agent = RunwayManagerAgent("runway_agent@localhost", "1234", atc_environment)

    await atc_agent.start()
    await aircraft_agent.start()
    await runway_agent.start()



if __name__ == "__main__":
    spade.run(main())


"""        addBehaviour(ForwardArrivalInfoToAirportBehavior.create(aircraft));
        addBehaviour(ConfigureVelocityBehavior.create(this, aircraft, 1000));
        addBehaviour(TakeOffBehavior.create(aircraft));
        addBehaviour(AcceptNewAirwayProposalBehavior.create(aircraft, finalDestination));
        addBehaviour(SetNewAirwayBehavior.create(aircraft, description));
        addBehaviour(LocationTickerBehavior.create(this, aircraft, 1000));
        addBehaviour(AdjustAltitudeBehavior.create(aircraft));"""
        
"""Request (request): Used to make a request, asking the receiver to perform some action or provide some information.

Inform (inform): Used to convey information from the sender to the receiver.

Propose (propose): Used to suggest something or make a proposal.

Query (query): Used to ask a question or query for information.

Subscribe (subscribe): Used to subscribe to a particular event or information.

Refuse (refuse): Used to refuse a request or decline a proposal."""
