# Instance File Format

## 1. File name

Every benchmark instance follows this naming pattern:

```text
MPVRP_A_sB_dC_pD.dat
```

| Field | Meaning |
| --- | --- |
| `A` | Instance number, from `001` to `150` |
| `B` | Number of service stations |
| `C` | Number of depots |
| `D` | Number of products |

For example:

```text
MPVRP_001_s48_d1_p1.dat
```

Each file has a matching counterpart in both benchmark scenarios. The version with changeover costs is used for the official evaluation. The zero-cost version contains the same fleet, locations, stocks, demands, and identifier, but all values in its transition matrix are zero.

## 2. General structure

An instance is a plain-text file. Its sections always appear in this order:

```text
# <uuid>
NbProducts NbDepots NbGarages NbStations NbVehicles
<product transition matrix>
<vehicles>
<depots>
<garages>
<service stations>
```

Values may be separated by spaces or tabs. Identifiers begin at `1` and must remain consecutive within each category. Apart from the identifier on the first line, the file should not contain comments or blank lines.

## 3. Instance identifier

The first line contains the unique identifier shared by the two versions of an instance:

```text
# c01ab718-9a2c-4a7d-bb95-f37e2a389409
```

## 4. Main dimensions

The second line gives the number of products, depots, garages, stations, and vehicles:

```text
NbProducts NbDepots NbGarages NbStations NbVehicles
```

For example, the following line describes an instance with 3 products, 2 depots, 1 garage, 20 stations, and 5 vehicles:

```text
3 2 1 20 5
```

## 5. Transition cost matrix

The next `NbProducts` lines form a square matrix:

```text
Cost_P1_to_P1 Cost_P1_to_P2 ...
Cost_P2_to_P1 Cost_P2_to_P2 ...
...
```

The value on row `p` and column `q` is the operational cost of preparing the vehicle to load product `q` when its current configuration is product `p`. This cost may include the loading setup itself; it is not limited to cleaning or changing the product.

All values must be finite and non-negative. The matrix may be asymmetric because the preparation required from `p` to `q` can differ from the preparation required from `q` to `p`. In the benchmark instances, the diagonal is zero, so loading the same product again adds no transition cost.

## 6. Vehicles

Each vehicle is described on one line:

```text
ID Capacity HomeGarage InitialProduct
```

- `ID` identifies the vehicle.
- `Capacity` is the maximum quantity it can carry and must be positive.
- `HomeGarage` identifies the garage where its schedule starts and ends.
- `InitialProduct` gives its product configuration before the first loading.

The initial product is important because the first loading cost is read from the transition matrix using this configuration as the starting point.

## 7. Depots

Each depot is described as follows:

```text
ID X Y Stock_P1 Stock_P2 ... Stock_Pn
```

`X` and `Y` are its coordinates. The remaining values give the available stock of each product. Stocks must be finite and non-negative, and the total stock of every product across all depots must cover total demand.

## 8. Garages

Each garage has an identifier and a position:

```text
ID X Y
```

Coordinates must be finite.

## 9. Service stations

Each station is described by:

```text
ID X Y Demand_P1 Demand_P2 ... Demand_Pn
```

Demand values must be finite and non-negative, and every station must request at least one product. Deliveries may be split between vehicles, but each station-product demand must be fully satisfied.

## 10. Complete example

```text
# c01ab718-9a2c-4a7d-bb95-f37e2a389409
2 1 2 3 2
0.0 18.1
61.5 0.0
1 20000 1 1
2 20000 1 2
1 81.6 63.6 57914 82626
1 98.1 49.6
2 56.8 26.0
1 23.5 42.2 0 4278
2 3.5 38.3 1344 2350
3 56.7 31.3 0 2319
```

This instance contains 2 products, 1 depot, 2 garages, 3 stations, and 2 vehicles. Vehicle 1 initially carries product 1, while vehicle 2 initially carries product 2.
