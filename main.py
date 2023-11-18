import spade
from runway import RunwayManagerAgent
from aircraft import AircraftAgent
from atc import AirTrafficControlAgent
from environment import Environment


async def main():
    # Create and initialize the environment
    atc_environment = Environment()
    
    atc_agent = AirTrafficControlAgent("atc_agent@localhost", "1234", atc_environment)
    
    aircraft_agent1 = AircraftAgent("aircraft_agent1@localhost", "1234", atc_environment, 100, 1)
    aircraft_agent2 = AircraftAgent("aircraft_agent2@localhost", "1234", atc_environment, 200, 3)
    aircraft_agent3 = AircraftAgent("aircraft_agent3@localhost", "1234", atc_environment, 300, 4)
    aircraft_agent4 = AircraftAgent("aircraft_agent4@localhost", "1234", atc_environment, 400, 4)
    runway_agent = RunwayManagerAgent("runway_agent@localhost", "1234", atc_environment)
    

    await atc_agent.start()
    await aircraft_agent1.start()
    await aircraft_agent2.start()
    await aircraft_agent3.start()
    await aircraft_agent4.start()
    await runway_agent.start()



if __name__ == "__main__":
    spade.run(main())