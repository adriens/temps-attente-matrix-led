---
config:
  theme: neutral
  themeVariables:
    background: '#ffffff'
  layout: fixed
---
flowchart TB
 subgraph s1["Phase démarrage"]
        D2("Chargement .env")
        D1("Démarrage matrice")
        D3("Connexion WiFi")
        D4("Synchro NTP")
        D5("API 1")
  end
 subgraph s2["Phase affichages"]
        SC2("Screen Info")
        SC1("Screen Accueil")
        SC3("Screen Légende")
        SC4("Screen Agences")
        SC5("Screen QR Code")
  end
 subgraph s3["Phase agences"]
        A1("Agences n")
        A2("API 2")
        A3("MaJ tps")
        A4("Old tps")
        A5("n+1=>n")
  end
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> D5
    D2 -. "Pas d'accès fichier .env" .-> E1("Erreur script 1")
    D3 -. 10 tentatives WiFi KO .-> E1
    D4 -. Echec NTP sur 3 URL .-> E1
    D5 -. Erreur API .-> E1
    D5 --> SC1
    SC1 -- Bouton C --> SC2
    SC2 -- Bouton C --> SC3
    SC3 -- Bouton C --> SC4
    SC4 -- Bouton C --> SC5
    SC5 -- Bouton C --> SC1
    SC4 --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A5
    A5 --> A1
    A2 -- KO MaJ tps --> A4
    A4 -- Reprise old tps --> A6("n+1=>n")
    A6 -- continuité boucle --> A1
    A2 -. 5 tentatives KO .-> E2("Erreur script 2")
    E1 --> R1("Redémarrage matrice")
    E2 --> R1
    F2("Bouton D") --> R1
     E1:::red
     E2:::red
     R1:::red
    classDef orange fill:#FFEACC,stroke:#f59e0b,stroke-width:2px,color:#000
    classDef blue fill:#0080ff,stroke:#DB2777,stroke-width:2px,color:#000
    classDef green fill:#E3FCEC, stroke:#2e7d32, stroke-width:2px, color:#000
    classDef red fill:#f8b4b4, stroke:#e53935, stroke-width:2px, color:#000
    style E2 stroke:#D50000
    style s1 fill:#E0FFE0,stroke:#00C853,stroke-width:2px;
    style s2 fill:#FFFFE0,stroke:#FFD600,stroke-width:2px;
    style s3 fill:#E0F7FF,stroke:#2962FF,stroke-width:2px;
    linkStyle 4 stroke:#D50000,fill:none
    linkStyle 5 stroke:#D50000,fill:none
    linkStyle 6 stroke:#D50000,fill:none
    linkStyle 7 stroke:#D50000,fill:none
    linkStyle 22 stroke:#D50000,fill:none
    linkStyle 23 stroke:#D50000,fill:none
    linkStyle 24 stroke:#D50000,fill:none
