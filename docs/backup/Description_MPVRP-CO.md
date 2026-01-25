**Description du problème**

Le Problème de Tournées de Véhicules Multi-Produits avec Coût de changement de Produit **(Multi-Product Multi-Depot Vehicule Routing Problem with Changeover Cost - MPVRP-CC)** combine des décisions de routage de véhicules, de gestion multi-produits et de planification opérationnelle dans un contexte de distribution de produits pétroliers.

Le problème prend en compte un ensemble de localisations comprenant plusieurs garages (bases des véhicules), plusieurs dépôts (points d'approvisionnement en produits), et un ensemble de stations-service (clients). Une flotte de camions-citernes est disponible, chaque camion ayant une capacité de chargement. Un ensemble de produits doit être distribué.

Chaque camion se voit attribuer initialement un produit au moment de la génération des instances. Chaque station-service exprime une demande pour chaque produit. Une matrice spécifie les distances entre toutes les paires de sites (garages, dépôts, stations-service). Un coût de changement de produit est appliqué lorsqu'un camion change de produit dans un dépôt.

Chaque camion effectue une tournée complète suivant le flux : **Garage → Boucle (Dépôt - Stations) → Garage**.

Une mini-tournée correspond à la séquence des stations visitées après un dépôt. Elle commence par un dépôt et se termine soit à un garage ou dépôt.

La tournée complète est composée d'une ou plusieurs mini-tournées :

- Chaque camion démarre de son garage attitré et doit retourner à la fin de sa tournée complète dans un garage.
- Une séquence d'opérations comprenant : (1) chargement d'un seul produit dans un dépôt, (2) livraisons aux stations-service, (3) retour à un dépôt pour le rechargement suivant.
- Un camion ne transporte qu'un seul type de produit par mini-tournée.
- Chaque camion se voit attribuer un produit initial avant même le début des tournées.
- Un camion peut changer de produit dans un dépôt (au début de sa tournée ou entre deux mini-tournées) moyennant un nettoyage qui engendre un coût. Ce changement peut s'effectuer dès la première visite à un dépôt ou lors de visites ultérieures.
- À la fin de chaque mini-tournée, un camion retourne à un dépôt pour se recharger en produit (du même type ou d'un type différent après changement de produit).

Le MPVRP-CO doit déterminer les tournées et mini-tournées pour tous les camions de manière à satisfaire des contraintes telles que :

- Chaque camion respecte sa capacité maximale lors de chaque mini-tournée.
- Les demandes de toutes les stations pour tous les produits doivent être satisfaites intégralement à la fin de toutes les tournées.
- La demande d'une station peut ne pas être entièrement satisfaite par un seul camion lors de son passage pour un produit donné.
- Un camion ne passe pas plus d'une fois par une même station pour le même produit.

On suppose que :

- Les dépôts disposent de stocks suffisants pour tous les produits.
- Tous les sites sont accessibles à tout moment.

Une solution optimale minimise le coût total comprenant :

- Le coût de transport, proportionnel à la distance totale parcourue par l'ensemble de la flotte sur toutes les tournées.
- Le coût engendré par tous les changements de produit effectués par les camions dans les dépôts.

Une solution réalisable doit garantir que:

- Chaque tournée de camion commence et se termine au garage du camion.
- Chaque mini-tournée respecte la contrainte de capacité du véhicule.
- Chaque mini-tournée ne transporte qu'un seul type de produit.
- Toutes les demandes des stations pour tous les produits sont satisfaites intégralement.