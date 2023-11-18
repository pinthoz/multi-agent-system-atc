from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import re
import asyncio
import random

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
                #await asyncio.sleep(2)
                msg = await self.receive()
                if msg:
                    if msg.body.startswith("Warning"):
                        
                        print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}.\nI will be attentive to any problems that may occur\n")
                    else:
                        position_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                        aircraft_id = int(re.search(r'\d+', msg.body).group())
                        #print("aircraft_id: ", aircraft_id)
                        if position_match:
                            x, y, z = map(float, position_match.groups())
                            self.agent.environment.aircraft_positions[aircraft_id] = (x, y, z)
                        print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")
                        # Handle the message here, e.g., provide instructions to the aircraft
        
        class WeatherConditions(CyclicBehaviour):
            async def run(self):
                await asyncio.sleep(3)
                bad_weather = random.randint(0, 15)
                if bad_weather == 5:
                    index = random.randint(0, len(self.agent.environment.weather_conditions)-1)
                    airport = list(self.agent.environment.weather_conditions)[index]
                    self.agent.environment.update_weather("bad", airport)
                    time = random.choice([20, 30, 40])
                    await asyncio.sleep(time)
                    self.agent.environment.update_weather("good", airport)

        

        # Add the behaviors to the agent
        self.add_behaviour(EnvironmentInteraction())
        self.add_behaviour(MessageHandling())
        self.add_behaviour(WeatherConditions())
            
