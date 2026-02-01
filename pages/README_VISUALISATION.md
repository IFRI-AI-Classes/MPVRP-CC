# Guide d'Utilisation - Visualisateur de Solutions VRP

Ce document explique comment utiliser l'interface de visualisation (`visualisation.html`) pour analyser graphiquement les instances et les solutions du problème de distribution de pétrole (MPVRP).

## 🚀 Lancement

L'outil est une application web autonome (Single Page Application). Pour l'utiliser :
1. Naviguez vers le dossier contenant le fichier `visualisation.html` (ex: `pages/visualisation.html`).
2. Ouvrez simplement ce fichier avec un navigateur web moderne (Google Chrome, Mozilla Firefox, Microsoft Edge, Safari).

Aucun serveur web ou installation Python n'est nécessaire pour la visualisation seule.

## 📂 Chargement des Données

L'interface dispose d'un panneau latéral gauche pour importer vos données par "Drag & Drop" (glisser-déposer) ou en cliquant sur les zones dédiées.

Il faut charger les fichiers dans l'ordre suivant (ou les deux) :

### 1. Fichier d'Instance (`.dat`, `.txt`)
Ce fichier définit la topologie du problème. Il permet de placer les nœuds sur la carte.
*   **Format attendu** : Format standard du projet MPVRP.
    *   Ligne 1 : Dimensions (ex: `nb_prod nb_depots nb_garages nb_stations nb_vehicules`)
    *   Matrice des coûts de changement (ignorée par la visus)
    *   Configuration des véhicules (ignorée par la visu)
    *   Liste des Dépôts (ID X Y)
    *   Liste des Garages (ID X Y)
    *   Liste des Stations (ID X Y Demandes...)

### 2. Fichier de Solution (`.dat`, `.txt`)
Ce fichier définit les trajets effectués par les camions.
*   **Format attendu** : Sortie textuelle du solveur.
    *   Lignes de route : `ID_Véhicule : SiteA - SiteB - SiteC ...`
    *   Métriques (optionnel, en fin de fichier) : Coût total, temps d'exécution, etc.

> **Note** : Si vous chargez une solution sans charger d'instance, la visualisation ne pourra pas afficher la carte car elle ne connaîtra pas les coordonnées des points.

## 🎮 Fonctionnalités de l'Interface

### Carte Interactive
*   **Visualisation** : Les nœuds sont affichés selon leur type avec des icônes distinctes.
*   **Animations** : Les camions se déplacent le long de leurs itinéraires.

### Légende des Symboles
*   🏢 **Garages** : Points de départ et de retour des camions (Couleur Violette).
*   🏭 **Dépôts** : Points de rechargement en produit (Couleur Cyan).
*   ⛽ **Stations** : Clients à livrer (Couleur Rose). Une jauge verte indique le taux de satisfaction de la demande au cours du temps.

### Panneau de Contrôle (Bas de page)
*   **Lecture / Pause** (`Space`) : Lance ou arrête l'animation des tournées.
*   **Pas à pas** : Boutons "Précédent" et "Suivant" pour avancer étape par étape.
*   **Reset** : Revient au début de l'animation.
*   **Timeline** : Glissière permettant de se déplacer instantanément à n'importe quel moment de la tournée.
*   **Vitesse** : Ajuste la vitesse de l'animation (de 0.25x à 4x).

### Statistiques & Informations
Le panneau latéral affiche en temps réel :
*   **Distance Totale** : Coût de la fonction objectif.
*   **Camions** : Nombre de véhicules utilisés.
*   **Segments** : Nombre total de trajets entre deux nœuds.
*   **Flotte** : Liste des camions actifs avec leur code couleur.

### Thèmes
Un bouton (☀️/🌙) en haut à droite permet de basculer entre le mode **Clair** (Light) et le mode **Sombre** (Dark) pour plus de confort visuel.
