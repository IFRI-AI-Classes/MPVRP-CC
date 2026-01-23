from dataclasses import dataclass
from typing import Dict


@dataclass
class Camion:
    id: str
    capacity: float
    garage_id: int
    initial_product: int

@dataclass
class Depot:
    id: str
    location: tuple  # (x, y)
    stocks: Dict[int, int]  # product_id -> quantity

@dataclass
class Garage:
    id: str
    location: tuple  # (x, y)

@dataclass
class Station:
    id: str
    location: tuple  # (x, y)
    demand: Dict[int, int]  # product_id -> quantity


@dataclass
class Instance:
    num_products: int
    num_camions: int
    num_depots: int
    num_garages: int
    num_stations: int
    camions: Dict[str, Camion]
    depots: Dict[str, Depot]
    garages: Dict[str, Garage]
    stations: Dict[str, Station]
    costs: Dict[tuple, float]  # (from_id, to_id) -> cost
    distances: Dict[tuple, float]  # (from_id, to_id) -> distance