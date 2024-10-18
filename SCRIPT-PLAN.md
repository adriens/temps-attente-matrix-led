# diagramme Mermaid pour représenter le fonctionnement du script 

```mermaid
flowchart TD

    %% Script de démarrage
    Start[Demarrage de la tablette <br> Lancement du script] --> Wifi_Check{Connexion <br> WIFI}

    %% Forme doc en jaune
    doc>"Fichier .env"]:::yellow --> | Récupération ID | Wifi_Check
    doc --> | Récupération clé |ApiKey_Check

    %% Formes {} en vert
    classDef green fill:#c2e59c,stroke:#2e7d32,stroke-width:2px;
    Wifi_Check{Connexion <br> WIFI}:::green
    NTP_Check{Synchronisation <br> NTP / GMT+11}:::green
    ApiKey_Check{Requete <br> API 1}:::green
    API2_Check{Requete <br> API 2}:::green
    ButtonB{Button B}:::green

    Wifi_Check -->|KO| Exit_Wifi[Affichage NO WIFI <br> => Sortie script]
    Wifi_Check -->|OK| NTP_Check

    NTP_Check -->|KO| Exit_NTP[Affichage NO NTP <br> => Sortie script]
    NTP_Check -->|OK| ApiKey_Check

    ApiKey_Check -->|KO| Exit_ApiKey[Affichage NO API <br> => Sortie script]
    ApiKey_Check -->|OK| Dico[Dictionnaire <br> agences]

    Dico --> API2_Check

    Exit_Wifi --> Reboot[Verifier config <br> Redémarrer tablette]
    Exit_ApiKey --> Reboot
    Exit_NTP --> Reboot

    API2_Check -->|KO <br> Pas de mise à jour du temps d'attente| ContinueNoUpdate[Poursuite du script <br> sans mise à jour]
    API2_Check -->|OK <br> Mise à jour du temps d'attente| ContinueUpdate[Poursuite du script <br> avec mise à jour]

    ContinueUpdate --> Affichage[Mise en place <br> affichage agence]
    ContinueNoUpdate --> Affichage

    %% Forcer l'alignement horizontal des smileys et du bloc Stop
    Affichage -->|temps moins de 5 min| Happy[Affichage <br> Smiley Happy] 
    Affichage -->|temps entre 5 et 10 min| Neutral[Affichage <br> Smiley Neutre] 
    Affichage -->|temps plus de 10 min| Sad[Affichage <br> Smiley Sad]
    Affichage <--> Stop[Pas d'incrément de l'index]

    Happy --> ButtonB
    Neutral --> ButtonB
    Sad --> ButtonB
    Stop <--> |actif| ButtonB
  
    ButtonB -->|inactif| Next[Incrément de l'index +1]
    Next --> API2_Check

    Scroll[Scroll Nom d'agence] --> Affichage
    Clock[Affichage Heure GMT+11] --> Affichage

    %% Formes rouges
    classDef red fill:#f8b4b4,stroke:#e53935,stroke-width:2px;
    Exit_Wifi:::red
    Exit_ApiKey:::red
    Exit_NTP:::red
    Reboot:::red

    %% Forme jaune
    classDef yellow fill:#fef08a,stroke:#f59e0b,stroke-width:2px;
