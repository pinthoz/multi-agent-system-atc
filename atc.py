from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import re
import asyncio
import random
from spade.message import Message

class AirTrafficControlAgent(Agent):
    '''
    Classe que define o agente de controlo de tráfego aéreo
    '''
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment
        self.priority_queue = {(41.72512, -7.46632, 0): [],
                               (41.23697, -8.67069, 0): [],
                               (39.84483, -7.44015, 0): [],
                               (38.78003, -9.13495, 0): [],
                               (37.02036, -7.96829, 0): []
                              }    

    async def setup(self):
        
        class FindClosestAirport(CyclicBehaviour):
            '''
            No caso de uma emergência, o ATC envia uma mensagem ao avião com o aeroporto mais próximo
            '''
            async def run(self):
                msg = await self.receive(timeout = 5)
                if msg and msg.body.startswith("Emergency"):
                    aircraft = str(msg.sender)
                    #print(f"\n{str(msg.sender)}\n")
                    partes = aircraft.split('@')
                    id_aircraft = partes[0]
                    number_id = re.search(r'\d+', id_aircraft).group()
                    aircraft_id = int(number_id) * 100
                    #print(aircraft_id)
                    reply = Message(to=str(msg.sender))
                    reply.set_metadata("performative", "inform")
                    new_destination = self.agent.environment.find_closest_airport(self.agent.environment.get_aircraft_position(aircraft_id))
                    reply.body = f"Ok go to {new_destination}"
                    #print(f"Go to {self.agent.environment.find_closest_airport(self.agent.environment.get_aircraft_position(aircraft_id))}")
                    if aircraft_id in self.agent.environment.priority_queue[new_destination]:
                        self.agent.environment.priority_queue[new_destination].remove(aircraft_id)
                        self.agent.environment.priority_queue[new_destination].insert(0, aircraft_id)
                    await self.send(reply)
                    
        
        class MessageHandling(CyclicBehaviour):
            '''
            Processa as mensagens enviadas pelos aviões quando estão próximos uns dos outros.
            '''
            async def run(self):
                #await asyncio.sleep(2)
                msg = await self.receive()
                if msg:
                    if msg.body.startswith("Warning"):
                        
                        print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}.\nI will be attentive to any problems that may occur\n")
                    elif msg.body.startswith("Aircraft"):
                        position_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                        aircraft_id = int(re.search(r'\d+', msg.body).group())
                        #print("aircraft_id: ", aircraft_id)
                        if position_match:
                            x, y, z = map(float, position_match.groups())
                            #self.agent.environment.update_aircraft_position(aircraft_id, (x, y, z))
                        print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")
                        # Handle the message here, e.g., provide instructions to the aircraft
        
        class WeatherConditions(CyclicBehaviour):
            '''
            Simula as condições meteorológicas.
            Por cada iteração, há uma probabilidade de 1/15 de ocorrer mau tempo.
            Se ocorrer mau tempo, é escolhido um aeroporto aleatório e as condições meteorológicas são atualizadas
            Durante um período de tempo aleatório entre 20 e 40 segundos, as condições meteorológicas são mantidas 
            (vamos considerar que só há mau tempo num aeroporto de cada vez).
            Passado esse período, as condições meteorológicas voltam ao normal.
            '''
            async def run(self):
                await asyncio.sleep(3)
                bad_weather = random.randint(0, 15)
                if bad_weather == 5:
                    index = random.randint(0, len(self.agent.environment.weather_conditions)-1)
                    airport = list(self.agent.environment.weather_conditions)[index]
                    self.agent.environment.update_weather("bad", airport)
                    time = random.randint(20, 40)
                    await asyncio.sleep(time)
                    self.agent.environment.update_weather("good", airport)
                    
        
        class IfisTheSameAirport(CyclicBehaviour):
            '''
            Verifica se, em caso de emergência, já tem um avião para aterrar antes dele no mesmo aeroporto
            '''
            async def run(self):
                msg = await self.receive(timeout=5)
                if msg and msg.body.startswith("I need to land"):
                    position_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                    if position_match == self.agent.destination:
                        reply = Message(to=str(msg.sender))
                        reply.set_metadata("performative", "inform")
                        reply.body = "You can land, i wait"
                        await self.send(reply)
        
        # Add the behaviors to the agent
        self.add_behaviour(MessageHandling())
        self.add_behaviour(WeatherConditions())
        self.add_behaviour(FindClosestAirport())
        self.add_behaviour(IfisTheSameAirport())

