# Exemple d'Instance MPVRP-CC

## Structure du fichier

### Ligne 0 : UUID (commentaire)
```
# 3f2a9c7e-6c2a-4a91-9f84-8c6c5e3b2f41
```
- Identifiant unique UUID v4 de l'instance
- Garantit l'unicité absolue de chaque fichier
- Ignoré par le parseur (ligne de commentaire `#`)

### Ligne 1 : Paramètres globaux
```
2  1  2  3  2
```
- **2** produits
- **1** dépôt
- **2** garages
- **3** stations (clients)
- **2** véhicules

### Bloc 2 : Matrice de coûts de transition (2×2)
```
0.0   18.1
61.5  0.0
```
- Produit 1 → Produit 1 : 0.0 (pas de contamination)
- Produit 1 → Produit 2 : 18.1
- Produit 2 → Produit 1 : 61.5
- Produit 2 → Produit 2 : 0.0

### Bloc 3 : Véhicules (2 véhicules)
```
ID  Capacité  Garage  Produit_initial
1   20000     1       1
2   20000     1       2
```

### Bloc 4 : Dépôts (1 dépôt)
```
ID  X     Y     Stock_P1  Stock_P2
1   81.6  63.6  57914     82626
```

### Bloc 5 : Garages (2 garages)
```
ID  X     Y
1   98.1  49.6
2   56.8  26.0
```

### Bloc 6 : Stations (3 clients)
```
ID  X     Y     Demande_P1  Demande_P2
1   23.5  42.2  0           4278
2   3.5   38.3  1344        2350
3   56.7  31.3  0           2319
```
- Station 1 : demande uniquement le produit 2
- Station 2 : demande les deux produits
- Station 3 : demande uniquement le produit 2