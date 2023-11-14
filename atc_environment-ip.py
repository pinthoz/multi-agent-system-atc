# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import math
from geopy.distance import geodesic




# Define the Environment class to represent the air traffic control environment
class Environment:
    def __init__(self):
        # Initialize environment variables, e.g., aircraft positions, weather, runways, etc.
        self.aircraft_positions = {100 : (41.23556,-8.67806,0)} # {aircraft_id: position-> (x, y, z)}
        self.weather_conditions = {} # {weather_data}
        self.runway_status = {1 : 1, 2:0} # {runway_id: status -> 0/1}

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
        # Retrieve one of runway id from the environment
        return 1


class AirTrafficControlAgent(Agent):
    def __init__(self, jid, password, environment, aircraft_id):
        super().__init__(jid, password)
        self.environment = environment
        self.aircraft_id = aircraft_id


    async def setup(self):
        # Define a behavior to perceive and interact with the environment
        class EnvironmentInteraction(CyclicBehaviour):
            async def run(self):

                # Perceive environment data - you can use ACL messages or other means
                aircraft_position = self.get_aircraft_position()
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
                print("RunwayAvailableInteraction behavior is running")
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
            
            async def send_instruction_to_aircraft(self, ):
                # Create an ACL message to send data to the air traffic control agent   
                msg = Message(to="atc_agent@localhost")  # Replace with the correct ATC agent JID
                msg.set_metadata("performative", "inform")
                msg.body = f"Aircraft {self.agent.aircraft_id} at position {position} requesting instructions.\nDistance to destination: {round(distance)} meters."
                
                if self.agent.reached_destination:
                    new_position = (position[0], position[1], 0)
                    msg.body = f"Aircraft {self.agent.aircraft_id} reached destination.{new_position}"


                # Send the message
                await self.send(msg)
        
        self.add_behaviour(RunwayAvailable())

class AircraftAgent(Agent):
    def __init__(self, jid, password, environment, aircraft_id, runway_id):
        super().__init__(jid, password)
        self.environment = environment
        self.aircraft_id = aircraft_id
        self.runway_id = runway_id
        self.reached_destination = False

    async def setup(self):
        # Define a behavior to interact with the environment and air traffic control
        class AircraftInteraction(CyclicBehaviour):
            async def run(self):
                print("AircraftInteraction behavior is running")
                # Perceive environment data
                aircraft_position = self.get_aircraft_position(self.agent.aircraft_id)
                
                new_position = self.move_towards(aircraft_position, (38.77944,-9.13611,0), 800, 50)
                
                distance_to_destination = geodesic((new_position[0], new_position[1]), (38.77944, -9.13611)).meters
                
                if distance_to_destination <= 1000:
                    #request runway availability
                    msg = Message(to="runway_agent@localhost")
                    msg.set_metadata("performative", "propose")
                    msg.body = f"Some runway available?"
                    
                    await self.send(msg)
                    msg2 = await self.receive()
                    print(msg2)
                    
                    if "is available" in msg2.body:
                        self.agent.reached_destination = True
                    
                    
                if not self.agent.reached_destination:
                    # Atualiza a posição da aeronave
                    self.agent.environment.update_aircraft_position(100, new_position)  
                    # Comunica com o controle de tráfego aéreo
                    await self.send_instruction_to_atc(aircraft_position, distance_to_destination)
                else:
                    new_position
                    await self.send_instruction_to_atc(aircraft_position, 0)
                    await asyncio.sleep(5)
                    

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
                    msg.body = f"Aircraft {self.agent.aircraft_id} reached destination.{new_position}"


                # Send the message
                await self.send(msg)
                
            
        

        # Add the behavior to the agent
        self.add_behaviour(AircraftInteraction())
    
        

async def main():
    # Create and initialize the environment
    atc_environment = Environment()
    atc_agent = AirTrafficControlAgent("atc_agent@localhost", "1234", atc_environment, 100)

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