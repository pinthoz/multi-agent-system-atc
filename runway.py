from spade.template import Template
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from airportDatabase import AirportDatabase
import re

class RunwayManagerAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment

    
    async def setup(self):
        class RunwayAvailable(CyclicBehaviour):
            async def run(self):
                airport_db = AirportDatabase()
                msg = await self.receive(timeout=5)
                if msg:
                    if template.match(msg):
                        # Handle the runway request message
                        print(f"Received runway request: {msg.body} from {msg.sender}")    
                        coordinates_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                        coordinates = tuple(map(float, coordinates_match.groups()))
                        requested_runway_id = self.agent.environment.get_runway_id(coordinates)
                        runway_is_available = self.get_runway_status(requested_runway_id)
                        if runway_is_available == 1:
                            # Create an ACL message to send data to the air traffic control agent
                            airport_id = self.agent.environment.get_airport_id(requested_runway_id)  # Assuming a method to get the airport ID
                            airport_name = airport_db.get_name(airport_id)
                            msg = Message(to=str(msg.sender))
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {requested_runway_id} at Airport {airport_name} is available."
                            # Include the airport ID in the message
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

           
        template = Template()
        template.set_metadata("performative", "propose")     
        
        self.add_behaviour(RunwayAvailable())