import time
import machine
import network
import ntptime
from cosmic import CosmicUnicorn
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN
import math

# Constantes pour les couleurs
COLORS = {
    'YELLOW': (255, 255, 0),
    'WHITE': (255, 255, 255),
    'BLUE': (0, 0, 255),
    'GREEN': (0, 255, 0),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'EYE_COLOR': (0, 0, 255)
}

class CosmicUnicornDisplay:
    """Classe pour gérer l'affichage sur l'écran Cosmic Unicorn"""

    def __init__(self):
        self.cu = CosmicUnicorn()
        self.graphics = PicoGraphics(display=DISPLAY_COSMIC_UNICORN)
        self.width, self.height = self.graphics.get_bounds()
        self.pens = {color: self.graphics.create_pen(*rgb) for color, rgb in COLORS.items()}

    def clear(self):
        """Efface l'écran"""
        self.cu.clear()

    def update(self):
        """Met à jour l'affichage"""
        self.cu.update(self.graphics)

    def set_pen(self, color):
        """Définit la couleur du stylo pour dessiner"""
        self.graphics.set_pen(self.pens[color])

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
        """Affiche l'heure au format HH:MM"""
        if synced:
            current_time = time.localtime(time.time() + 11 * 3600)
        else:
            elapsed_time = time.time() - start_time
            current_time = time.localtime(start_time + elapsed_time)
        hour = "{:02}".format(current_time[3])
        minute = "{:02}".format(current_time[4])
        self.display_digit(hour[0], 14, 1, 'WHITE')
        self.display_digit(hour[1], 18, 1, 'WHITE')
        self.graphics.set_pen(self.pens['WHITE'])
        self.graphics.pixel(22, 3)
        self.graphics.pixel(22, 4)
        self.display_digit(minute[0], 24, 1, 'WHITE')
        self.display_digit(minute[1], 28, 1, 'WHITE')

    def draw_smiley(self, mood):
        """
        Dessine un smiley avec une expression donnée ('happy', 'neutral', 'sad').
        Le smiley est dessiné sur une zone spécifique de l'affichage.
        """
        # Coordonnées du visage jaune (contour du cercle du visage)
        smiley_coords_yellow = [
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

        # Coordonnées des yeux et de la bouche (différentes selon l'humeur)
        eyes_coords = [
            # Coordonnées des yeux (fixes)
            (11, 13), (12, 13), (13, 13), (18, 13), (19, 13), (20, 13),
            (11, 14), (12, 14), (13, 14), (18, 14), (19, 14), (20, 14)
        ]

        mouth_coords = {
            'happy': [(13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (14, 20), (15, 20), (16, 20), (17, 20)],
            'neutral': [(14, 19), (15, 19), (16, 19), (17, 19)],
            'sad': [(13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20), (14, 19), (15, 19), (16, 19), (17, 19)]
        }

        # Dessiner le visage jaune
        self.set_pen('YELLOW')
        for x, y in smiley_coords_yellow:
            self.graphics.pixel(x, y)

        # Dessiner les yeux en noir
        self.set_pen('BLACK')
        for x, y in eyes_coords:
            self.graphics.pixel(x, y)

        # Dessiner la bouche en fonction de l'humeur
        self.set_pen('BLACK')
        for x, y in mouth_coords[mood]:
            self.graphics.pixel(x, y)

def connect_wifi(ssid, password):
    """Connexion au Wi-Fi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi Connected")

def sync_time():
    """Synchronisation de l'heure avec un serveur NTP"""
    try:
        ntptime.host = 'pool.ntp.org'
        ntptime.settime()
        print("Heure synchronisée via NTP")
        return True
    except OSError as e:
        print("Erreur de synchronisation NTP :", e)
        return False

def scroll_text(display):
    """Affiche un texte défilant"""
    PADDING = 5
    MESSAGE = "Agence Centrale"
    STEP_TIME = 0.075

    display.graphics.set_font("bitmap5")
    msg_width = display.graphics.measure_text(MESSAGE, 1)
    shift = 0
    last_time = time.ticks_ms()

    while True:
        time_ms = time.ticks_ms()
        if time_ms - last_time > STEP_TIME * 1000:
            shift += 1
            if shift >= (msg_width + PADDING * 2) - display.width:
                shift = 0
            last_time = time_ms

        display.set_pen('BLACK')
        display.graphics.rectangle(0, 26, display.width, 5)  # Efface juste cette zone

        display.set_pen('WHITE')
        display.graphics.text(MESSAGE, PADDING - shift, 25, -1, 1)

        display.update()
        time.sleep(0.001)

def main_loop(display, start_time, synced, waiting_time):
    """Boucle principale pour l'affichage"""
    while True:
        display.clear()

        # Dessiner les cadres
        display.draw_frame(0, 6, 'YELLOW')
        display.draw_frame(25, 31, 'YELLOW')

        # Afficher le texte "OPT"
        display.draw_text_opt()

        # Afficher l'horloge
        display.display_clock(start_time, synced)

        # Déterminer l'humeur du smiley en fonction du temps d'attente
        if waiting_time < 5:
            mood = 'happy'
        elif 5 <= waiting_time < 10:
            mood = 'neutral'
        else:
            mood = 'sad'

        # Dessiner le smiley correspondant
        display.draw_smiley(mood)

        # Afficher le texte défilant
        scroll_text(display)

        display.update()
        time.sleep(0.05)

# Connexion Wi-Fi
connect_wifi('TP-Link_F41E', '27611708')

# Tentative de synchronisation NTP
synced = sync_time()
start_time = time.time()

# Initialiser l'affichage
display = CosmicUnicornDisplay()

# Exemple de variable représentant le temps d'attente
waiting_time = 7  # Exemple : peut être récupéré via une API

# Lancer la boucle principale
main_loop(display, start_time, synced, waiting_time)

