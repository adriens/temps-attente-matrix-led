import time
import network
import ntptime
import urequests as requests
from cosmic import CosmicUnicorn
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN
import os

# Constantes pour les couleurs
COLORS = {
    'YELLOW': (251, 189, 8),
    'WHITE': (255, 255, 255),
    'BLUE': (40, 44, 131),
    'GREEN': (0, 255, 0),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'EYE_COLOR': (0, 0, 255),
    'GREEN_SMILEY': (34, 177, 76),
    'YELLOW_SMILEY': (255, 242, 0),
    'RED_SMILEY': (237, 28, 36)
}

def load_api_key(file_path):
    """Charge la clé API depuis un fichier .env"""
    try:
        with open(file_path, "r") as f:
            for line in f:
                print(f"Ligne lue : {line.strip()}")  # Debugging : afficher chaque ligne lue
                if line.startswith("API_KEY"):
                    api_key = line.strip().split('=')[1]
                    print(f"Clé API extraite : {api_key}")  # Debugging : afficher la clé API extraite
                    return api_key
    except OSError:
        print(f"Erreur : impossible de trouver ou lire le fichier {file_path}")
    return None

# Lister le contenu du répertoire courant d'exécution du script
print("Contenu du répertoire courant:", os.listdir())

# Utilisation du fichier .env pour obtenir la clé API
api_key = load_api_key("api_key.env")

if not api_key:
    print("Erreur : Clé API non trouvée.")
else:
    print(f"Clé API trouvée : {api_key}")

class CosmicUnicornDisplay:
    """Classe pour gérer l'affichage sur l'écran Cosmic Unicorn"""

    def __init__(self):
        self.cu = CosmicUnicorn()
        self.graphics = PicoGraphics(display=DISPLAY_COSMIC_UNICORN)
        self.width, self.height = self.graphics.get_bounds()
        self.pens = {color: self.graphics.create_pen(*rgb) for color, rgb in COLORS.items()}
        self.scroll_shift = 0  # Déplacement du texte défilant
        self.last_scroll_time = time.ticks_ms()  # Dernière mise à jour du texte défilant
        self.transition_var = ''  # Variable de transition pour afficher un nom à la fois
        self.graphics.set_font("bitmap5")  # Définir la police pour le texte

    def clear(self):
        """Efface l'écran avec un fond noir"""
        self.graphics.set_pen(self.pens['BLACK'])
        self.graphics.clear()

    def update(self):
        """Met à jour l'affichage"""
        self.cu.update(self.graphics)

    def set_pen(self, color):
        """Définit la couleur du stylo pour dessiner"""
        self.graphics.set_pen(self.pens[color])

    def scroll_text(self, message):
        """Affiche un texte défilant dans la frame 3 """
        PADDING = 5
        STEP_TIME = 0.1  # Temps en secondes entre chaque mouvement de défilement

        msg_width = self.graphics.measure_text(message, 1)  # Mesurer la largeur du texte
        time_ms = time.ticks_ms()  # Obtenir le temps actuel en millisecondes

        # Vérifier si assez de temps s'est écoulé avant de faire défiler
        if time_ms - self.last_scroll_time > STEP_TIME * 1000:
            self.scroll_shift += 1
            # Remettre à zéro le décalage si le texte a complètement défilé hors de l'écran
            if self.scroll_shift >= msg_width + self.width + PADDING:
                self.scroll_shift = -self.width  # Redémarrer depuis la droite de l'écran
            self.last_scroll_time = time_ms

        # Effacer la zone du texte défilant uniquement dans les lignes 27 à 32 (6 lignes au total)
        self.set_pen('BLACK')
        self.graphics.rectangle(0, 26, self.width, 6)  # Effacer la zone du texte défilant

        # Afficher le texte avec le décalage calculé
        self.set_pen('WHITE')
        self.graphics.text(message, PADDING - self.scroll_shift, 26, -1, 1)

        # Mettre à jour l'affichage pour afficher les changements
        self.update()

    def draw_frame(self, y_start, y_end, color):
        """Dessine un cadre rectangulaire autour de l'affichage"""
        self.set_pen(color)
        for x in range(0, self.width):
            self.graphics.pixel(x, y_start)  # Ligne supérieure
            self.graphics.pixel(x, y_end)    # Ligne inférieure
        for y in range(y_start, y_end + 1):
            self.graphics.pixel(0, y)         # Colonne gauche
            self.graphics.pixel(self.width - 1, y)  # Colonne droite

    def draw_text_opt(self):
        """Affiche le texte 'OPT' sur les lignes spécifiées"""
        self.set_pen('BLUE')
        o_coords = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 5), (3, 1), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)]
        p_coords = [(6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (7, 1), (7, 3), (8, 1), (8, 2), (8, 3)]
        t_coords = [(10, 1), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5), (12, 1)]
        for coords in [o_coords, p_coords, t_coords]:
            for x, y in coords:
                self.graphics.pixel(x, y)

    def draw_smiley(self, mood):
        """Dessine un smiley avec une expression donnée ('happy', 'neutral', 'sad')."""
        smiley_coords = [
            (14, 8), (15, 8), (16, 8), (17, 8),  # Ligne 8
            (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 9), (19, 9),  # Ligne 9
            (11, 10), (12, 10), (13, 10), (14, 10), (15, 10), (16, 10), (17, 10), (18, 10), (19, 10), (20, 10),
            (10, 11), (11, 11), (12, 11), (13, 11), (14, 11), (15, 11), (16, 11), (17, 11), (18, 11), (19, 11), (20, 11), (21, 11),  # Ligne 11
            (9, 12), (10, 12), (11, 12), (12, 12), (13, 12), (14, 12), (15, 12), (16, 12), (17, 12), (18, 12), (19, 12), (20, 12), (21, 12), (22, 12),  # Ligne 12
            (9, 13), (10, 13), (11, 13), (12, 13), (13, 13), (14, 13), (15, 13), (16, 13), (17, 13), (18, 13), (19, 13), (20, 13), (21, 13), (22, 13),  # Ligne 13
            (8, 14), (9, 14), (10, 14), (11, 14), (12, 14), (13, 14), (14, 14), (15, 14), (16, 14), (17, 14), (18, 14), (19, 14), (20, 14), (21, 14), (22, 14), (23, 14),  # Ligne 14
            (8, 15), (9, 15), (10, 15), (11, 15), (12, 15), (13, 15), (14, 15), (15, 15), (16, 15), (17, 15), (18, 15), (19, 15), (20, 15), (21, 15), (22, 15), (23, 15),  # Ligne 15
            (8, 16), (9, 16), (10, 16), (11, 16), (12, 16), (13, 16), (14, 16), (15, 16), (16, 16), (17, 16), (18, 16), (19, 16), (20, 16), (21, 16), (22, 16), (23, 16),  # Ligne 16
            (8, 17), (9, 17), (10, 17), (11, 17), (12, 17), (13, 17), (14, 17), (15, 17), (16, 17), (17, 17), (18, 17), (19, 17), (20, 17), (21, 17), (22, 17), (23, 17),  # Ligne 17
            (9, 18), (10, 18), (11, 18), (12, 18), (13, 18), (14, 18), (15, 18), (16, 18), (17, 18), (18, 18), (19, 18), (20, 18), (21, 18), (22, 18),  # Ligne 18
            (9, 19), (10, 19), (11, 19), (12, 19), (13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (19, 19), (20, 19), (21, 19), (22, 19),  # Ligne 19
            (10, 20), (11, 20), (12, 20), (13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20), (19, 20), (20, 20), (21, 20),  # Ligne 20
            (11, 21), (12, 21), (13, 21), (14, 21), (15, 21), (16, 21), (17, 21), (18, 21), (19, 21), (20, 21),  # Ligne 21
            (12, 22), (13, 22), (14, 22), (15, 22), (16, 22), (17, 22), (18, 22), (19, 22),  # Ligne 22
            (14, 23), (15, 23), (16, 23), (17, 23), # Ligne 23
        ]
        eyes_coords = [
            (11, 13), (12, 13), (13, 13), (18, 13), (19, 13), (20, 13),
            (11, 14), (12, 14), (13, 14), (18, 14), (19, 14), (20, 14)
        ]
        mouth_coords = {
            'happy': [(13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (14, 20), (15, 20), (16, 20), (17, 20)],
            'neutral': [(14, 19), (15, 19), (16, 19), (17, 19)],
            'sad': [(14, 19), (15, 19), (16, 19), (17, 19),(13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20)]
        }
        mood_color = {
            'happy': 'GREEN_SMILEY',
            'neutral': 'YELLOW_SMILEY',
            'sad': 'RED_SMILEY'
        }

        self.set_pen(mood_color[mood])
        for x, y in smiley_coords:
            self.graphics.pixel(x, y)
        self.set_pen('BLACK')
        for x, y in eyes_coords:
            self.graphics.pixel(x, y)
        for x, y in mouth_coords[mood]:
            self.graphics.pixel(x, y)

    def display_digit(self, digit, col_start, row_start, color):
        """Affiche un chiffre à une position donnée"""
        self.set_pen(color)
        digits = {
            '0': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
            '1': [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)],
            '2': [(0, 0), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 4), (2, 0), (2, 1), (2, 2), (2, 4)],
            '3': [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (1, 4), (0, 4), (1, 2), (0, 2)],
            '4': [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (2, 1), (2, 0)],
            '5': [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (1, 4), (0, 4)],
            '6': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (2, 3), (2, 2), (1, 2)],
            '7': [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
            '8': [(0, 0), (1, 0), (2, 0), (0, 2), (2, 2), (0, 4), (1, 4), (2, 4), (0, 1), (2, 1), (0, 3), (2, 3)],
            '9': [(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2), (2, 1), (2, 3), (2, 4), (0, 1), (1, 4), (0, 4)]
        }
        for dx, dy in digits[digit]:
            self.graphics.pixel(col_start + dx, row_start + dy)

    def display_clock(self, start_time, synced):
        """Affiche l'heure au format HH:MM avec un décalage de GMT+11."""
        # Ajouter 11 heures (11 * 3600 secondes) au temps actuel pour obtenir l'heure GMT+11
        if synced:
            current_time = time.localtime(time.time() + 11 * 3600)
        else:
            current_time = time.localtime(start_time + 11 * 3600)
            
        hour = "{:02}".format(current_time[3])
        minute = "{:02}".format(current_time[4])
        self.display_digit(hour[0], 14, 1, 'WHITE')
        self.display_digit(hour[1], 18, 1, 'WHITE')
        self.graphics.set_pen(self.pens['WHITE'])
        self.graphics.pixel(22, 3)
        self.graphics.pixel(22, 4)
        self.display_digit(minute[0], 24, 1, 'WHITE')
        self.display_digit(minute[1], 28, 1, 'WHITE')
        
    def set_transition_variable(self, name):
        """Mise à jour de la variable de transition avec un nom d'agence."""
        self.transition_var = name
        self.scroll_shift = 0  # Remettre le décalage à 0 pour chaque nouveau nom

    def display_message_frame_2(self, message):
        """Affiche un message statique dans la Frame 2."""
        PADDING = 2
        self.set_pen('BLACK')
        self.graphics.rectangle(0, 12, self.width, 12)  # Efface la zone de la frame 2 (ligne 12 à 24)
        self.set_pen('WHITE')
        # Afficher le texte centré dans la frame 2
        text_width = self.graphics.measure_text(message, 1)
        self.graphics.text(message, (self.width - text_width) // 2, 14, -1, 1)
        self.update()

def check_network_connection():
    """Effectue un test simple de connexion réseau"""
    try:
        # Essai d'une requête vers un service externe fiable (comme Google)
        response = requests.get('http://clients3.google.com/generate_204', timeout=5)
        if response.status_code == 204:  # Code 204 = No Content, signifie succès
            return True
    except Exception as e:
        print(f"Erreur de connexion réseau : {e}")
    return False

def get_agency_data(api_key):
    """Requête l'API et retourne un tableau avec ID, Nom, Temps d'attente."""
    url = "https://api.opt.nc/temps-attente-agences/csv"
    headers = {
        "x-apikey": api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=120)
        if response.status_code == 200:
            # Afficher la réponse brute pour vérifier ce qui est retourné
            print(f"Réponse brute de l'API : {response.content}")
            
            # Vérifier si le contenu est non vide
            if not response.content:
                print("Erreur : Réponse vide de l'API")
                return None
            
            # Essayer de décoder la réponse en UTF-8
            try:
                csv_data = response.content.decode('utf-8')
                return parse_csv_data(csv_data)
            except UnicodeDecodeError as e:
                print(f"Erreur de décodage UTF-8 : {e}")
                return None
        else:
            print(f"Erreur : statut de la requête {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de la requête API : {e}")
    return None


def parse_csv_data(csv_content):
    """Analyse le CSV et retourne un tableau avec ID, Nom et Temps d'attente"""
    rows = csv_content.split("\n")
    data = [row.split(",") for row in rows[1:] if row.strip()]  # Diviser et nettoyer les lignes

    tableau_agences = []

    for row in data:
        agence_id = row[0].strip()  # ID de l'agence
        designation = row[1].strip().replace("Agence de ", "").upper()  # Nom de l'agence sans "Agence de" et en majuscules
        realMaxWaitingTimeMs = int(row[2].strip())  # Temps d'attente en millisecondes

        # Ajouter chaque agence dans le tableau (3 colonnes : ID, Nom, Temps d'attente)
        tableau_agences.append([agence_id, designation, realMaxWaitingTimeMs])

    return tableau_agences

def connect_wifi(ssid, password):
    """Connexion au Wi-Fi avec gestion des erreurs."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    for _ in range(10):  # Essayer de se connecter pendant 10 secondes
        if wlan.isconnected():
            print(f"WiFi Connected, IP: {wlan.ifconfig()[0]}")
            return True
        time.sleep(1)
    print("Pas de connexion WiFi.")
    return False

def sync_time():
    """Synchronisation de l'heure avec un serveur NTP (en GMT+11)."""
    ntp_servers = ['time.windows.com', 'ntp1.google.com', 'pool.ntp.org']

    for server in ntp_servers:
        try:
            ntptime.host = server
            ntptime.settime()  # Synchronisation de l'heure avec UTC
            print(f"Heure synchronisée via NTP avec {server}")
            return True
        except OSError as e:
            print(f"Erreur de synchronisation NTP avec {server}: {e}")

    print("Tous les serveurs NTP ont échoué, utilisation de l'heure locale.")
    return False

def main_loop(display, start_time, synced):
    """Boucle principale pour l'affichage des données d'agences et l'heure."""

    # Tester la connexion réseau
    if not check_network_connection():
        print("Pas de connexion WAN")
        display.display_message_frame_2("NO WAN")  # Afficher "NO WAN" si pas de connexion
        time.sleep(5)
        return

    # Synchroniser l'heure via NTP
    sync_time()

    # Afficher "WAIT" pendant la requête API
    display.display_message_frame_2("WAIT")
    time.sleep(2)

    # Appel de la fonction avec la clé API
    tableau_agences = get_agency_data(api_key)

    if not tableau_agences:
        display.display_message_frame_2("NO API")
        time.sleep(5)
        return

    current_index = 0  # Initialiser l'index pour parcourir les agences

    while True:
        # Parcourir chaque agence dans le tableau
        agence_id, name, waiting_time = tableau_agences[current_index]

        # Afficher les informations dans la console pour suivi
        print(f"Agence ID: {agence_id}, Nom: {name}, Temps d'attente: {waiting_time // 60000} minutes")

        # Déterminer l'humeur du smiley en fonction du temps d'attente
        if waiting_time < 300000:
            mood = 'happy'
        elif 300000 <= waiting_time < 600000:
            mood = 'neutral'
        else:
            mood = 'sad'

        # Dessiner les cadres et le texte "OPT"
        display.clear()
        display.draw_frame(0, 6, 'YELLOW')  # Cadre en haut (Frame 1)
        display.draw_text_opt()  # Texte "OPT"

        # Dessiner le smiley correspondant à l'humeur
        display.draw_smiley(mood)

        # Faire défiler le nom de l'agence dans la Frame 3
        display.set_transition_variable(name)
        for _ in range(100):  # Faire défiler pendant 5 secondes (50 * 0.1 sec)
            display.scroll_text(display.transition_var)
            display.display_clock(start_time, synced)  # Afficher l'heure
            time.sleep(0.1)

        # Passer à l'agence suivante
        current_index = (current_index + 1) % len(tableau_agences)


# Connexion Wi-Fi
wifi_connected = connect_wifi('TP-Link_F41E', '27611708')

# Initialiser l'affichage
display = CosmicUnicornDisplay()

# Lancer la boucle principale pour faire défiler les noms d'agences
start_time = time.time()
main_loop(display, start_time, wifi_connected)




