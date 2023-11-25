from spade.template import Template
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from airportDatabase import AirportDatabase
import re

class RunwayManagerAgent(Agent):
    '''
    Classe que define o agente que controla as pistas de aterragem
    '''
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment

    
    async def setup(self):
        class RunwayAvailable(CyclicBehaviour):
            '''
            Processa as mensagens enviadas pelos aviões.
            Verifica se tem pista de aterragem disponível.
            '''
            async def run(self):
                airport_db = AirportDatabase()
                msg = await self.receive()
                if msg:
                    if template.match(msg):
                        # Recebe as coordenadas do aeroporto e verifica se tem uma pista disponível
                        print(f"Received runway request: {msg.body} from {msg.sender}")    
                        coordinates_match = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', msg.body)
                        coordinates = tuple(map(float, coordinates_match.groups()))
                        requested_runway_id = self.agent.environment.get_runway_id(coordinates)
                        runway_is_available = self.get_runway_status(requested_runway_id)
                        if runway_is_available == 1:
                            # Se tem uma pista disponível, envia uma mensagem ao avião com o ID da pista e o nome do aeroporto
                            airport_id = self.agent.environment.get_airport_id(requested_runway_id)  
                            airport_name = airport_db.get_name(airport_id)
                            msg = Message(to=str(msg.sender))
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {requested_runway_id} at Airport {airport_name} is available."
                            await self.send(msg)
                        else:
                            msg = Message(to=str(msg.sender))
                            msg.set_metadata("performative", "inform")
                            msg.body = f"Runway {requested_runway_id} is not available."
                            await self.send(msg)

            def get_runway_status(self, runway_id):
                # Verifica o estado da pista de aterragem
                status = self.agent.environment.get_runway_status(runway_id)
                return status

           
        template = Template()
        template.set_metadata("performative", "propose")     
        
        self.add_behaviour(RunwayAvailable())