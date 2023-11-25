# Classe com os nomes dos aeroportos
class AirportDatabase:
    def __init__(self):
        self.airports = {
            (41.72512, -7.46632, 0): "Aerodromo de Chaves",
            (41.23697, -8.67069, 0): "Aeroporto do Porto",
            (39.84483, -7.44015, 0): "Aerodromo de Castelo Branco",
            (38.78003, -9.13495, 0): "Aeroporto Humberto Delgado",
            (37.02036, -7.96829, 0): "Aeroporto de Faro"
        }

    # Retorna o nome dos aeroportos
    def get_name(self, coordinates):
        return self.airports.get(coordinates)
    
    # Retorna as coordenas do aeroporto
    def get_coor(self, index):
        return list(self.airports)[index]
