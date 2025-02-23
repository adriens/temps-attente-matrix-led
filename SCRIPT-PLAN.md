```mermaid
flowchart TD

%% Optionnel : initialisation d'un thème clair (pour forcer le fond blanc)
%%{init: {'theme':'neutral', 'themeVariables': {'background':'#ffffff'}}}%%

flowchart TB

%% Définition des classes de couleurs
classDef green fill:#E3FCEC,stroke:#2e7d32,stroke-width:2px,color:#000
classDef orange fill:#FFEACC,stroke:#f59e0b,stroke-width:2px,color:#000
classDef pink fill:#FFD9E8,stroke:#DB2777,stroke-width:2px,color:#000
classDef red fill:#f8b4b4,stroke:#e53935,stroke-width:2px,color:#000

%% Sous-graphe 1 : Phase de démarrage
subgraph S1[Phase de démarrage]
direction TB
    SM1(Démarrage matrice)
    SM2(Chargement .env)
    SM3(Connexion WiFi)
    SM4(Synchronisation NTP)

    SM1 --> SM2
    SM2 --> SM3
    SM3 --> SM4
end
class S1 green

%% Sous-graphe 2 : Écrans principaux
subgraph S2[Écrans Principaux]
direction TB
    SA(Screen Accueil)
    SI(Screen Info)
    SL(Screen Légende)
    SG(Screen Agences)
    SQ(Screen QR Code)

    SA --> SI
    SI --> SL
    SL --> SG
    SG --> SQ
end
class S2 orange

%% Sous-graphe 3 : Gestion des Agences
subgraph S3[Gestion des Agences]
direction TB
    A1(Agences n)
    A2(Ancien Temps)
    A3(Appel API2)
    A4(Mise à jour du Temps)
    A5(Affichage)

    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
end
class S3 pink

%% Liens entre les sous-graphes
S1 --> S2
S2 --> S3

%% Gestion des erreurs et sorties
E1(Erreur script<br>Sortie)
class E1 red

SM2 -- "Pas d'accès .env" --> E1
SM3 -- "10 tentatives KO" --> E1
SM4 -- "KO" --> E1
A3 -- "KO" --> E1
A4 -- "8 tentatives" --> E1
