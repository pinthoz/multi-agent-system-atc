from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
import asyncio
from geopy.distance import geodesic
import random
import math
import re
from airportDatabase import AirportDatabase


class AircraftAgent(Agent):
    '''
    O AircraftAgent e composto por:
    - Pelo environment
    - Id do aviao
    - Id da pista
    - Um booleano que indica se ja chegou ao destino
    - Um booleano que indica se fez um desvio
    - Coordenadas do aviao
    - Coordenadas do destino
    - Um booleano que indica se ja aterrou
    - Um booleano que indica se tem algum problema
    - Distancia percorrida
    - Um booleano que indica se fez um pedido de aterragem
    - Um "booleano inteiro" que indica se tem prioridade ou nao
    
    '''
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
        self.landed = False
        self.problem = False
<<<<<<< Updated upstream
=======
        self.request_land = False
        self.priority = 0
>>>>>>> Stashed changes

        
    async def setup(self):
        
        class AircraftInteraction(CyclicBehaviour):
            async def run(self):
                
                #Enquanto o aviao esta no ar
                if not self.agent.landed:
                
                    await asyncio.sleep(2)
                    distance_to_other_aircraft = 1000000
                    
                    # Verifica se o aviao esta muito proximo de outro aviao atraves das coordenadas
                    for other_aircraft_id in self.agent.environment.aircraft_positions:
                        if other_aircraft_id != self.agent.aircraft_id:
                            #Verifica atraves do "gps" as coordenadas dos outros avioes
                            other_aircraft_position = self.agent.environment.get_aircraft_position(other_aircraft_id)
                            #Calcula a distancia entre ele e outro aviao
                            distance_to_other_aircraft = geodesic(
                                (self.agent.aircraft_position[0], self.agent.aircraft_position[1]),
                                (other_aircraft_position[0], other_aircraft_position[1])
                            ).kilometers
                            #Se a distancia for menor que 50 km e o outro aviao nao estiver pousado faz uma manobra de desvio
                            if distance_to_other_aircraft < 50 and other_aircraft_position[2] != 0:
                                print(f"Aircraft {self.agent.aircraft_id} is too close to Aircraft {other_aircraft_id}. Performing avoidance maneuver.")
                                new_position = self.perform_avoidance_manoeuver(self.agent.aircraft_position, other_aircraft_position)
                                new_position_with_altitude = (new_position[0], new_position[1], new_position[2]- 500) # Faz o desvio e desce em altitude para garantir que nao bate
                                self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position_with_altitude)
                                self.agent.change_route = True  


                    #Se o aviao fez um desvio envia uma mensagem ao atc para este ficar a par do ocorrido
                    if self.agent.change_route:
                        msg = Message(to="atc_agent@localhost")
                        msg.set_metadata("performative", "inform")
                        msg.body = f"Warning! Aircraft {self.agent.aircraft_id} is too close to another aircraft. Performing avoidance maneuver."
                        self.agent.change_route = False
                        await self.send(msg)
                
                #Quando ja aterrou inicia uma nova rota para um novo aeroporto
                else:
                    
                    self.agent.environment.update_aircraft_position(self.agent.aircraft_id, self.agent.destination)
                    airport_db = AirportDatabase()
                    old_runway = self.agent.runway_id
                    old_airport = self.agent.destination
                    index = random.randint(0, 4)
                    new_airport = airport_db.get_coor(index)
                    while new_airport == old_airport: # Como o index e random pode calhar o mesmo aeroporto
                        index = random.randint(0, 4)
                        new_airport = airport_db.get_coor(index)     
                    #Inicia tudo para comecar uma nova viagem 
                    runway = self.agent.environment.get_new_runway(new_airport)
                    self.agent.runway_id = runway
                    self.agent.destination = new_airport
<<<<<<< Updated upstream
                    self.agent.landed = False
                    
=======

                   
                            
>>>>>>> Stashed changes
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
                                #print(f"Aircraft {self.agent.aircraft_id} received a response from {response.sender}: {response.body}")
                                if str(response.body) == "Yes":
                                    print(f"I'm Waiting... Aircraft {self.agent.aircraft_id}")
                                    await asyncio.sleep(5)
                                    print(f"End of waiting... Aircraft {self.agent.aircraft_id}")

                    while (self.agent.environment.get_weather_data(old_airport)) == "bad":
                        await asyncio.sleep(1)
                    airport_db = AirportDatabase()
                    print(f"Aircraft {self.agent.aircraft_id} started a new trip to {airport_db.get_name(self.agent.destination)}")    
                    self.agent.landed = False
                    self.agent.reached_destination = False
                    #Atualiza o valor da runway para 1 uma vez que ja saiu da pista
                    self.agent.environment.update_runway_status(old_runway, 1)
                    

            # Funcao para calcular as coordenadas obtidas pelo desvio
            def perform_avoidance_manoeuver(self, current_position, other_aircraft_position):
                # Realizar a manobra de desvio para aumentar a distancia
                avoidance_strength = 1.2
                # Formula para o calculo do angulo entre a posicao atual e a posicao do outro aviao para o desvio
                angle = math.atan2(other_aircraft_position[1] - current_position[1],
                                other_aircraft_position[0] - current_position[0])
                # Calculo do vetor de desvio usando a forca de desvio e as funcoes trigonometricas
                avoidance_vector = (
                    avoidance_strength * math.cos(angle),
                    avoidance_strength * math.sin(angle)
                )
                # Aplicacao do vetor obtido sobre a posicao atual
                new_position = (
                    current_position[0] + avoidance_vector[0],
                    current_position[1] + avoidance_vector[1],
                    current_position[2] 
                )

                return new_position
            


        #Quando o aviao esta quase a chegar ao aeroporto, arranja uma runway livre, caso haja
        class AircraftInteractionRunway(CyclicBehaviour):
            async def run(self):

                #Enquanto o aviao esta no ar
                if not self.agent.landed:
                    
                    await asyncio.sleep(2)

                    # Atualiza a sua posicao no percurso
                    self.agent.aircraft_position = self.get_aircraft_position(self.agent.aircraft_id)
                    new_position = self.move_towards(self.agent.aircraft_position, self.agent.destination, 1000000, 100)
                    distance_to_destination = geodesic((new_position[0], new_position[1]), (self.agent.destination[0], self.agent.destination[1])).meters
                    
                    # Atraves das coordenadas, obtem o nome dos aeroportos
                    airport_db = AirportDatabase()
                    airport_name = airport_db.get_name(self.agent.destination)
                    
                    # Se a distancia for menor que 6000 metros comunica com o runway para lhe atribuir uma pista 
                    if distance_to_destination <= 6000 :
                        if not self.agent.reached_destination:
                            msg = Message(to="runway_agent@localhost")
                            msg.set_metadata("performative", "propose")
                            msg.body = f"Some runway available for aeroport {airport_name} : {self.agent.destination}?"
                            
<<<<<<< Updated upstream
                            await self.send(msg)
=======
                            # Se o aviao deteta que esta mau tempo no aeroporto de destino, comunica com o atc para aterrar no aeroporto mais perto 
                            if self.agent.environment.get_weather_data(self.agent.destination) == "bad":
                                new_destination = self.agent.environment.find_closest_airport(self.agent.destination)
                                msg = Message(to="runway_agent@localhost")
                                msg.set_metadata("performative", "propose")
                                msg.body = f"Some runway available for aeroport {airport_db.get_name(new_destination)} : {new_destination}?"
                                await self.send(msg)
                                self.agent.destination = new_destination
                            # Se o tempo esta bom, faz um pedido ao runway_agent para lhe atribuir uma pista para o aeroporto de destino
                            else:
                                msg = Message(to="runway_agent@localhost")
                                msg.set_metadata("performative", "propose")
                                msg.body = f"Some runway available for aeroport {airport_name} : {self.agent.destination}?"
                                
                                await self.send(msg)
                                '''
                                msg_to_atc = Message(to="atc_agent@localhost")
                                msg_to_atc.set_metadata("performative", "request")
                                msg_to_atc.body =f"Can I land at {self.agent.destination} ?"

                                await self.send(msg_to_atc)
                                '''
                            if self.check_priority(self.agent.aircraft_id, self.agent.destination):
                                self.agent.priority = 1
    


>>>>>>> Stashed changes
                            
                    # Enquanto nao aterra, atualiza a posicao    
                    if not self.agent.reached_destination:
                        self.agent.environment.update_aircraft_position(self.agent.aircraft_id, new_position)  
                        await self.send_instruction_to_atc(self.agent.aircraft_position, distance_to_destination)
<<<<<<< Updated upstream
                    else:
=======
                    # Quando aterra 
                    elif self.agent.reached_destination and self.agent.priority == 1:
                        # Atualiza a ocupacao do runway e informa a posicao ao atc

>>>>>>> Stashed changes
                        await self.land_aircraft()
                        print(self.agent.environment.runway_status)
                        await self.send_instruction_to_atc(self.agent.aircraft_position, 0)
                        #Aterrou
                        self.agent.landed = True   
                        self.agent.priority = 0
                

            def check_priority(self, aircraft_id, destination):
                #print(destination)
                if (aircraft_id not in self.agent.environment.priority_queue[destination]):
                    self.agent.environment.priority_queue[destination].append(aircraft_id)
                #print(self.agent.environment.priority_queue)
                #print(self.agent.environment.priority_queue[destination][0])
                if self.agent.environment.priority_queue[destination][0] == aircraft_id:
                    del self.agent.environment.priority_queue[destination][0]
                    return True
                elif len(self.agent.environment.priority_queue[destination]) > 1 and self.agent.environment.priority_queue[destination][1] == aircraft_id and len(self.agent.environment.get_runway_id(destination)) > 1:
                    del self.agent.environment.priority_queue[destination][0]
                    return True
                else:
                    return False
            # Atualiza a posicao do aviao no environment
            def get_aircraft_position(self, aircraft_id):
                return self.agent.environment.get_aircraft_position(aircraft_id)
            
            # Funcao de movimento do aviao
            def move_towards(self, current_position, destination_position, velocity, dt):
                if not self.agent.landed:
                    current_coord = (current_position[0], current_position[1])
                    destination_coord = (destination_position[0], destination_position[1])

                    # Calcula a distancia dadas as coordenadas
                    distance = geodesic(current_coord, destination_coord).meters
                    
                    # Se for 0 retorna a posicao de destino
                    if distance == 0:
                        return destination_position

                    # Calcula o tempo estimado para atingir o destino com base na velocidade do aviao
                    time_to_destination = distance / velocity

<<<<<<< Updated upstream

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
=======
                    # Calcula a proporcao para determinar a nova posicaoo intermediaria com base no tempo (dt)
                    ratio = 1.0 / (time_to_destination * dt)
                    new_position = (
                        current_position[0] + ratio * (destination_position[0] - current_position[0]),
                        current_position[1] + ratio * (destination_position[1] - current_position[1]),
                        9000 
                    )
                    
                    return new_position
>>>>>>> Stashed changes
            
            # Envia mensagem da sua posicao ao atc
            async def send_instruction_to_atc(self, position,distance):
                msg = Message(to="atc_agent@localhost")
                msg.set_metadata("performative", "inform")
                #msg.body = f"Aircraft {self.agent.aircraft_id} at position {position}.\nDistance to destination: {round(distance)} meters."
                
                # Atraves das coordenadas, obtem o nome dos aeroportos
                airport_db = AirportDatabase()
                airport_name = airport_db.get_name(self.agent.destination)

                # Se ja chegou ao destino envia mensagem ao atc
                if self.agent.reached_destination:
                    new_position = (position[0], position[1], 0)
                    msg.body = f"Aircraft {self.agent.aircraft_id} reached destination at runway {self.agent.runway_id} in {new_position} at {airport_name}."

                    await self.send(msg)

            # Atualiza os valores das runways no environment
            async def land_aircraft(self):
                self.agent.environment.update_runway_status(self.agent.runway_id, 0)

        # Classe para simular um problema no aviao
        class AnyProblem(PeriodicBehaviour):
            async def run(self):
                if not self.agent.landed:
                    have_problem = random.randint(0, 25)
                    if have_problem == 5:
                        self.agent.problem = True

                
        # Lida com a mensagem recebida do runway_agent que se for is available, aterra naquela pista        
        class MessageHandling(CyclicBehaviour):
            async def run(self):
                msg = await self.receive()
                if msg:
                    if "is available" in msg.body:
                        runway_id = int(re.search(r'\d+', msg.body).group())
                        self.agent.runway_id = runway_id
                        self.agent.reached_destination = True
                        
<<<<<<< Updated upstream
                    elif "new route started" in msg.body:

                        self.agent.new_route_event.set()

                    #print(f"Hi! {msg.to} received message: {msg.body} from {msg.sender}\n")
                    
=======
            
>>>>>>> Stashed changes
        class SendMessageAirport(CyclicBehaviour):
            """
                Recebe mensagem do aviao que pergunta se algum dos outros vai para o mesmo
                destino dele.
                Os outros avioes enviam respostas Yes ou No de acordo com o seu destino 
            """
            async def run(self):
                # Se alguem pediu as coordenadas dos outros avioes recebe a mensagem dele
                if (self.agent.environment.has_1_value(self.agent.environment.request_coord)):
                    msg = await self.receive(timeout=10)
                    if msg and "aircraft_agent" in str(msg.sender) and msg.metadata["performative"] == "query":
                        #print(f"Recebeu mensagem de {msg.sender} com conteudo {msg.body}")

                        # Envia uma resposta ao remetente original usando o JID
                        response = Message(to=msg.metadata["reply-to"])
                        response.set_metadata("performative", "inform")
                        # Recolhe as coordenadas da mensagem
                        cord = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', str(msg.body))
                        #Se as coordenadas recebidas forem iguais ao destino reponde Yes
                        if (self.agent.destination == (float(cord.group(1)), float(cord.group(2)), int(cord.group(3)))): 
                            response.body = "Yes"
                        else:
                            response.body = "No"
                        await self.send(response)
                        #print(f"Aircraft {self.agent.aircraft_id} sent a response to {msg.sender}: {response.body}")
                    # Como o pedido ja foi resolvido coloca o dicionario a 0
                    self.agent.environment.update_all_request_coord_to_0()
<<<<<<< Updated upstream

=======
                    
        # Quando um aviao tem um problema, avisa os outros avioes e recebe qual e o aeroporto mais proximo
        class Emergency(CyclicBehaviour):
            async def run(self):
                if self.agent.problem:
                    await asyncio.sleep(2)
                    airport_db = AirportDatabase()
                    request_airport = Message(to=f"atc_agent@localhost")
                    request_airport.set_metadata("performative", "request")
                    request_airport.body = "Emergency! Find me the closest airport"
                    await self.send(request_airport)
                    airport_request= await self.receive(timeout=10)
                    
                    # Se a mensagem recebida foi enviada pelo atc obtem o aeroporto mais proximo
                    if airport_request and airport_request.metadata["performative"] == "inform" and "atc" in str(airport_request.sender) and not airport_request.body.startswith("You can land"):
                        print(f"Recebeu mensagem de {airport_request.sender} com conteudo {airport_request.body}")
                        cord = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', str(airport_request.body))
                        closest_airport = (float(cord.group(1)), float(cord.group(2)), int(cord.group(3)))

                        # Avisa todos os avioes o seu novo destino
                        for other_aircraft_id in self.agent.environment.aircraft_positions:
                            if other_aircraft_id != self.agent.aircraft_id:
                                request = Message(to=f"aircraft_agent{str(other_aircraft_id)[0]}@localhost")
                                request.set_metadata("performative", "emergency")
                                request.body = f"Emergency: I need to land in {airport_db.get_name(closest_airport)} : {closest_airport}! Please, let me land!"
                                #print(f"I need to land in {airport_db.get_name(closest_airport)} : {closest_airport}")
                                await self.send(request)
                        
                        self.agent.request_land = True
                        self.agent.destination = closest_airport
                        self.agent.problem = False
        
        # Recebe a mensagem do aviao com problemas
        class Emergency_Airport(CyclicBehaviour):
            async def run(self):
                if self.agent.request_land:
                    msg = await self.receive(timeout=10)
                    if msg and "aircraft_agent" in str(msg.sender) and msg.metadata["performative"] == "emergency" and msg.body.startswith("Emergency: I need to land"):
                        print(f"Recebeu mensagem de {msg.sender} com conteudo {msg.body}")

                        # Envia uma resposta ao remetente original usando o JID do campo "reply-to"
                        response = Message(to=str(msg.sender))
                        response.set_metadata("performative", "inform")
                        # Obtem as coordenadas do novo aeroporto do aviao com problemas
                        cord = re.search(r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+)\)', str(msg.body))
                        # Se o aeroporto for o mesmo, o aviao que recebeu a mensagem espera
                        if (self.agent.destination == (float(cord.group(1)), float(cord.group(2)), int(cord.group(3)))): 
                            response.body = "I wait for you"
                            #print("ver isto")
                            #print(response.body)
                            #logica para ele esperar o outro aviao pousar
                        
                        else:
                            response.body = "No"
                        await self.send(response)
                        
                        #print(f"Aircraft {self.agent.aircraft_id} sent a response to {msg.sender}: {response.body}")
                    self.agent.request_land = False
        

                    
>>>>>>> Stashed changes
        # Add the behavior to the agent
        self.add_behaviour(AircraftInteractionRunway())
        self.add_behaviour(MessageHandling())
        self.add_behaviour(AircraftInteraction())
<<<<<<< Updated upstream
        self.add_behaviour(AnyProblem())
        self.add_behaviour(SendMessageAirport())
=======
        self.add_behaviour(AnyProblem(10))
        self.add_behaviour(SendMessageAirport())
        self.add_behaviour(Emergency())
        self.add_behaviour(Emergency_Airport())
>>>>>>> Stashed changes
