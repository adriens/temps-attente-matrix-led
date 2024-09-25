import time
import machine
import network
import ntptime
from cosmic import CosmicUnicorn
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN
import math

# Initialisation de l'écran Cosmic Unicorn
cu = CosmicUnicorn()
graphics = PicoGraphics(display=DISPLAY_COSMIC_UNICORN)

# Obtenir la largeur et la hauteur de l'affichage
width, height = graphics.get_bounds()

# Paramètres pour les couleurs
YELLOW = graphics.create_pen(255, 255, 0)  # Jaune pour le cadre
WHITE = graphics.create_pen(255, 255, 255)  # Blanc pour l'heure et le texte
BLUE = graphics.create_pen(0, 0, 255)     # Bleu pour le lettrage "OPT"
GREEN = graphics.create_pen(0, 255, 0)    # Vert pour le cercle du visage
BLACK = graphics.create_pen(0, 0, 0)      # Noir pour nettoyer l'écran
RED = graphics.create_pen(255, 0, 0)      # Rouge pour la bouche
EYE_COLOR = graphics.create_pen(0, 0, 255)  # Bleu pour les yeux

# Connexion au Wi-Fi (à adapter avec les identifiants)
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi Connected")

# Synchronisation de l'heure via NTP
def sync_time():
    try:
        ntptime.host = 'pool.ntp.org'  # Serveur NTP (peut être changé)
        ntptime.settime()
        print("Heure synchronisée via NTP")
        return True  # Synchronisation réussie
    except OSError as e:
        print("Erreur de synchronisation NTP :", e)
        return False  # Synchronisation échouée, on bascule sur l'heure interne

# Fonction pour dessiner le cadre (Frame 1 et Frame 3)
def draw_frame(y_start, y_end, color):
    graphics.set_pen(color)
    for x in range(0, width):
        graphics.pixel(x, y_start)  # Ligne supérieure
        graphics.pixel(x, y_end)    # Ligne inférieure
    for y in range(y_start, y_end + 1):
        graphics.pixel(0, y)         # Colonne gauche
        graphics.pixel(width - 1, y)  # Colonne droite

# Fonction pour afficher "O", "P", "T" sur les lignes 3 à 5
def draw_text_opt():
    graphics.set_pen(BLUE)
    o_coords = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 5), (3, 1), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)]
    for x, y in o_coords:
        graphics.pixel(x, y)
    p_coords = [(6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (7, 1), (7, 3), (8, 1), (8, 2), (8, 3)]
    for x, y in p_coords:
        graphics.pixel(x, y)
    t_coords = [(10, 1), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5), (12, 1)]
    for x, y in t_coords:
        graphics.pixel(x, y)

# Fonction pour afficher un chiffre à une position précise
def display_digit(digit, col_start, row_start, color):
    graphics.set_pen(color)
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
        graphics.pixel(col_start + dx, row_start + dy)

# Afficher l'horloge HH:MM dans la zone colonne 14 à 30 et lignes 1 à 5
def display_clock(start_time, synced):
    if synced:
        current_time = time.localtime(time.time() + 11 * 3600)
    else:
        elapsed_time = time.time() - start_time
        current_time = time.localtime(start_time + elapsed_time)
    hour = "{:02}".format(current_time[3])
    minute = "{:02}".format(current_time[4])
    display_digit(hour[0], 14, 1, WHITE)
    display_digit(hour[1], 18, 1, WHITE)
    graphics.set_pen(WHITE)
    graphics.pixel(22, 3)
    graphics.pixel(22, 4)
    display_digit(minute[0], 24, 1, WHITE)
    display_digit(minute[1], 28, 1, WHITE)

# Fonction pour le texte défilant dans Frame 3
def scroll_text_in_frame_3():
    PADDING = 5
    MESSAGE_COLOUR = (255, 255, 255)
    OUTLINE_COLOUR = (0, 0, 0)
    BACKGROUND_COLOUR = (0, 0, 0)
    MESSAGE = "Agence Centrale"
    HOLD_TIME = 2.0
    STEP_TIME = 0.075

    graphics.set_font("bitmap5")  # Utiliser une police adaptée
    msg_width = graphics.measure_text(MESSAGE, 1)
    shift = 0
    last_time = time.ticks_ms()

    while True:
        time_ms = time.ticks_ms()
        if time_ms - last_time > STEP_TIME * 1000:
            shift += 1
            if shift >= (msg_width + PADDING * 2) - width:
                shift = 0
            last_time = time_ms

        graphics.set_pen(graphics.create_pen(int(BACKGROUND_COLOUR[0]), int(BACKGROUND_COLOUR[1]), int(BACKGROUND_COLOUR[2])))
        graphics.rectangle(0, 26, width, 5)  # Efface juste cette zone

        graphics.set_pen(graphics.create_pen(int(MESSAGE_COLOUR[0]), int(MESSAGE_COLOUR[1]), int(MESSAGE_COLOUR[2])))
        graphics.text(MESSAGE, PADDING - shift, 25, -1, 1)

        cu.update(graphics)

        time.sleep(0.001)  # Petite pause

# Fonction pour dessiner un smiley dans la "frame 2" (lignes 9 à 22)
# Coordonnées du visage jaune (centré sur une grille 32x32)
# Décalage pour centrer sur une grille 32x32 (commence à (8,8))
smiley_coords_yellow = [
    # Contour et remplissage du visage (cercle complet en 15x15 LED)
    (14, 8), (15, 8), (16, 8), (17, 8), # Ligne 8
    (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 9), (19, 9),  # Ligne 9
    (11, 10), (12, 10), (13, 10), (14, 10), (15, 10), (16, 10), (17, 10), (18, 10), (19, 10), (20, 10),  # Ligne 10
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

# Coordonnées des yeux et de la bouche (en noir)
smiley_coords_black = [
    # Yeux
    (11, 13), (12, 13), (13, 13), (18, 13), (19, 13), (20, 13),
    (11, 14), (12, 14), (13, 14), (18, 14), (19, 14), (20, 14),
    (11, 15), (12, 15), (13, 15), (18, 15), (19, 15), (20, 15),
    # Bouche
    (13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19),
    (14, 20), (15, 20), (16, 20), (17, 20),
]

# Dessiner le visage jaune
graphics.set_pen(YELLOW)
for x, y in smiley_coords_yellow:
    graphics.pixel(x, y)

# Dessiner les yeux et la bouche en noir
graphics.set_pen(BLACK)
for x, y in smiley_coords_black:
    graphics.pixel(x, y)


# Fonction pour la boucle principale
def main_loop(start_time, synced):
    while True:
        cu.clear()

        # Dessiner les cadres
        draw_frame(0, 6, YELLOW)   # Frame 1 (ligne 1 à 7)
        draw_frame(25, 31, YELLOW) # Frame 3 (ligne 26 à 30)

        # Afficher "OPT" dans Frame 1
        draw_text_opt()

        # Afficher l'horloge dans l'espace spécifié (colonne 14 à 30, lignes 1 à 5)
        display_clock(start_time, synced)

        # Appel à la fonction de défilement de texte dans la Frame 3
        scroll_text_in_frame_3()

        cu.update(graphics)
        time.sleep(0.05)

# Connexion Wi-Fi
connect_wifi('TP-Link_F41E', '27611708')

# Tentative de synchronisation NTP
synced = sync_time()
start_time = time.time()

# Lancer la boucle principale
main_loop(start_time, synced)
