from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from geopy.distance import geodesic
import asyncio

class AirTrafficControlAgent(Agent):
    
    async def setup(self):
        print("Air Traffic Control Agent started")
        
        # Behaviors
        self.add_behaviour(self.ReceiveMessages())
        self.add_behaviour(self.SendMessages())
        self.add_behaviour(self.CalculateDistance())
        self.add_behaviour(self.ReceiveAdminMessages())
        
        self.flight_has_arrived = False
    
    class ReceiveMessages(CyclicBehaviour):
        async def run(self):
            msg = await self.receive()
            if msg:
                print(f"Received message: {msg.body}")
                reply = Message(to=msg.sender)
                reply.body = "Message received"
                await self.send(reply)
                
                
    class ReceiveAdminMessages(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"Received message from admin: {msg.body}")


    async def send_distance(self, distance):
        msg = Message(to="aircraft0@localhost")  # Change to the actual recipient JID
        msg.body = f"Distance to airport: {distance} km"
    
    
    class SendMessages(CyclicBehaviour):
        async def run(self):
            msg = Message(to="admin@localhost") 
            msg.body = "Hello from Air Traffic Control Agent"
            await self.send(msg)
            await asyncio.sleep(1)
    
    class CalculateDistance(CyclicBehaviour):
        async def run(self):
            airport_location = (38.6413, 80.7781)
            current_location = (40.7128, 74.0060)
            speed = 800  # km/h
            time_spent = 0  # hours
            has_arrived = False

            while not has_arrived:
                distance = geodesic(airport_location, current_location).km
                distance -= speed * time_spent
                if distance <= 0:
                    print('---------------------')
                    print("| Arrived at airport |")
                    print('---------------------')
                    self.flight_has_arrived = True
                    has_arrived = True
                else:
                    await self.send_distance(distance)
                    time_spent += 1
                    await asyncio.sleep(1)
                

        async def send_distance(self, distance):
            msg = Message(to="aircraft0@localhost")  # Change to the actual recipient JID
            msg.body = f"Distance to airport: {distance} km"
            await self.send(msg)

    async def run(self):
        try:
            await asyncio.gather(
                self.ReceiveMessages().run(),
                self.SendMessages().run(),
                self.CalculateDistance().run(),
                self.ReceiveAdminMessages().run(),
            )
        except asyncio.CancelledError:
            pass  
        except Exception as e:
            print(f"Agent stopped with exception: {e}")
        
    class ReceiveAdminMessages(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"Received message from admin: {msg.body}")
                
                
class AircraftAgent(Agent):
    
    async def setup(self):
        print("Aircraft Agent (aircraft0) started")
        self.add_behaviour(self.ReceiveMessages())
        self.add_behaviour(self.ReceiveAdminMessages())
    
    class ReceiveMessages(CyclicBehaviour):
        async def run(self):
            msg = await self.receive()
            if msg:
                print(f"Received message: {msg.body}")

    class ReceiveAdminMessages(CyclicBehaviour):
        async def run(self):
            msg = await self.receive()
            if msg:
                if msg.sender == "admin@localhost":
                    print(f"Received message from admin: {msg.body}")


if __name__ == "__main__":
    agent = AirTrafficControlAgent("admin@localhost", "pinthoz")
    agent2 = AircraftAgent("aircraft0@localhost", "aviao")
    asyncio.run(agent.start())
    asyncio.run(agent2.start())