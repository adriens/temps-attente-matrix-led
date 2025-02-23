flowchart TD

    %% Script de démarrage
    Start[Démarrage matrice LED<br>Lancement du script] --> Wifi_Check{Connexion<br>WIFI}

    %% Forme doc en jaune
    doc["Fichier .env"]:::yellow --> |Récupération ID| Wifi_Check
    doc --> |Récupération clé| ApiKey_Check

    %% Formes en vert
    classDef green fill:#c2e59c,stroke:#2e7d32,stroke-width:2px;
    Wifi_Check:::green
    NTP_Check{Synchronisation<br>NTP / GMT+11}:::green
    ApiKey_Check{Requête<br>API 1}:::green
    API2_Check{Requête<br>API 2}:::green
    ButtonB{Bouton B}:::green

    Wifi_Check -->|KO| Exit_Wifi[Affichage<br>NO WIFI<br>=> Sortie script]
    Wifi_Check -->|OK| NTP_Check

    NTP_Check -->|KO| Exit_NTP[Affichage<br>NO NTP<br>=> Sortie script]
    NTP_Check -->|OK| ApiKey_Check

    ApiKey_Check -->|KO| Exit_ApiKey[Affichage<br>NO API<br>=> Sortie script]
    ApiKey_Check -->|OK| Dico[Dictionnaire<br>agences]

    Dico --> API2_Check

    Exit_Wifi --> Reboot[Vérifier config<br>Redémarrer matrice]
    Exit_ApiKey --> Reboot
    Exit_NTP --> Reboot

    API2_Check -->|KO| ContinueNoUpdate[Sans mise à jour<br>Temps d'attente]
    API2_Check -->|OK| ContinueUpdate[Avec mise à jour<br>Temps d'attente]

    ContinueUpdate --> Affichage[Mise en place<br>affichage agence]
    ContinueNoUpdate --> Affichage

    %% Alignement horizontal des smileys et du bloc Stop
    Affichage -->|< 5 min| Happy[Affichage<br>Smiley Happy] 
    Affichage -->|5 à 10 min| Neutral[Affichage<br>Smiley Neutre] 
    Affichage -->|> 10 min| Sad[Affichage<br>Smiley Sad]
    Affichage <--> Stop[Pas d'incrément<br>de l'index]

    Happy --> ButtonB
    Neutral --> ButtonB
    Sad --> ButtonB
    Stop <--> ButtonB

    ButtonB -->|inactif| Next[Incrément de l'index +1]
    Next --> API2_Check

    Scroll[Défilement<br>Nom d'agence] --> Affichage
    Clock[Affichage<br>Heure GMT+11] --> Affichage

    %% Formes rouges
    classDef red fill:#f8b4b4,stroke:#e53935,stroke-width:2px;
    Exit_Wifi:::red
    Exit_ApiKey:::red
    Exit_NTP:::red
    Reboot:::red

    %% Forme jaune
    classDef yellow fill:#fef08a,stroke:#f59e0b,stroke-width:2px;
