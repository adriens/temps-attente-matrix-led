import time
import network
import ntptime
import urequests as requests
import os
import gc
import _thread
import machine
from cosmic import CosmicUnicorn
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN

# Constantes pour les couleurs utilisées dans l'affichage
COLORS = {
    'YELLOW': (251, 189, 8),
    'WHITE': (255, 255, 255),
    'BLUE': (40, 44, 131),
    'GREEN': (0, 255, 0),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'GREEN_SMILEY': (34, 177, 76),
    'YELLOW_SMILEY': (255, 242, 0),
    'RED_SMILEY': (237, 28, 36)
}

# Classe pour gérer l'affichage sur l'écran Cosmic Unicorn
class CosmicUnicornDisplay:
    def __init__(self):
        """Initialise l'affichage, les stylos, le statut du son, la luminosité et le volume."""
        self.cu = CosmicUnicorn()
        self.graphics = PicoGraphics(display=DISPLAY_COSMIC_UNICORN)
        self.width, self.height = self.graphics.get_bounds()
        self.pens = {color: self.graphics.create_pen(*rgb) for color, rgb in COLORS.items()}
        self.scroll_shift = 0
        self.last_scroll_time = time.ticks_ms()
        self.transition_var = ''
        self.graphics.set_font("bitmap4")
        self.sound_enabled = True  # Statut du son activé/désactivé
        self.brightness = 0.5  # Luminosité initiale
        self.loop_paused = False  # Variable de pause pour le bouton B
        self.volume = 500  # Fréquence initiale du bip
        self.pause_led_position = (1, 25)  # Position de la LED de pause
        self.led_positions_on = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # LED quand son activé
        self.led_positions_off_red = [(0, 9), (1, 10), (2, 11), (3, 12)]  # LED rouges quand son désactivé
        self.led_positions_off_blue = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # LED bleues quand son désactivé
        self.channel = self.cu.synth_channel(5)  # Canal synth pour le bip sonore
        self.cu.set_brightness(self.brightness)
        self.update_led_sound_status(self.sound_enabled)  # Initialiser les LEDs du son
        print("Affichage initialisé avec succès")

    def clear(self):
        """Efface l'écran sans toucher aux LEDs du son et de pause."""
        self.graphics.set_pen(self.pens['BLACK'])
        self.graphics.clear()
        # Ne pas effacer les LEDs du son et de pause
        self.update_led_sound_status(self.sound_enabled)
        if self.loop_paused:
            self.set_pen('YELLOW')
            self.graphics.pixel(*self.pause_led_position)
        self.update()

    def update(self):
        """Met à jour l'affichage."""
        self.cu.update(self.graphics)

    def set_pen(self, color):
        """Définit la couleur du stylo graphique."""
        self.graphics.set_pen(self.pens[color])

    def scroll_text(self, message):
        """Gère le défilement du texte sur l'écran."""
        PADDING = 5
        STEP_TIME = 0.1
        msg_width = self.graphics.measure_text(message, 1)
        time_ms = time.ticks_ms()

        if time_ms - self.last_scroll_time > STEP_TIME * 1000:
            self.scroll_shift += 1
            if self.scroll_shift >= msg_width + self.width + PADDING:
                self.scroll_shift = -self.width
            self.last_scroll_time = time_ms

        self.set_pen('BLACK')
        self.graphics.rectangle(0, 26, self.width, 6)
        self.set_pen('WHITE')
        self.graphics.text(message, PADDING - self.scroll_shift, 26, -1, 1)
        self.update()

    def draw_frame(self, y_start, y_end, color):
        """Dessine un cadre autour du smiley."""
        self.set_pen(color)
        for x in range(0, self.width):
            self.graphics.pixel(x, y_start)
            self.graphics.pixel(x, y_end)
        for y in range(y_start, y_end + 1):
            self.graphics.pixel(0, y)
            self.graphics.pixel(self.width - 1, y)
        self.update()

    def draw_text_opt(self):
        """Affiche le texte OPT NC sur la partie gauche de l'écran."""
        self.set_pen('BLUE')
        o_coords = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 5), (3, 1), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)]
        p_coords = [(6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (7, 1), (7, 3), (8, 1), (8, 2), (8, 3)]
        t_coords = [(10, 1), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5), (12, 1)]
        for coords in [o_coords, p_coords, t_coords]:
            for x, y in coords:
                self.graphics.pixel(x, y)
        self.update()

    def draw_smiley(self, mood):
        """Dessine un smiley en fonction de l'humeur (happy, neutral, sad) sans effacer les LEDs du son."""
        # Effacement seulement de la zone du smiley
        self.set_pen('BLACK')
        self.graphics.rectangle(7, 7, 19, 19)  # Smiley area, sans toucher aux LEDs du son

        smiley_coords = [
            (13, 8), (14, 8), (15, 8), (16, 8), (17, 8), (18, 8),
            (11, 9), (12, 9), (13, 9), (18, 9), (19, 9), (20, 9),
            (10, 10), (11, 10), (20, 10), (21, 10),
            (9, 11), (10, 11), (21, 11), (22, 11),
            (8, 12), (9, 12), (22, 12), (23, 12),
            (8, 13), (23, 13),
            (7, 14), (8, 14), (23, 14), (24, 14),
            (7, 15), (24, 15),
            (7, 16), (24, 16),
            (7, 17), (24, 17),
            (7, 18), (24, 18),
            (7, 19), (8, 19), (23, 19), (24, 19),
            (8, 20), (23, 20),
            (8, 21), (9, 21), (22, 21), (23, 21),
            (9, 22), (10, 22), (21, 22), (22, 22),
            (10, 23), (11, 23), (20, 23), (21, 23),
            (11, 24), (12, 24), (13, 24), (18, 24), (19, 24), (20, 24),
            (13, 25), (14, 25), (15, 25), (16, 25), (17, 25), (18, 25),
        ]
        eyes_coords = [
            (11, 14), (12, 14), (13, 14), (18, 14), (19, 14), (20, 14),
            (11, 15), (12, 15), (13, 15), (18, 15), (19, 15), (20, 15)
        ]
        mouth_coords = {
            'happy': [(12, 19), (13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (19, 19), (13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20)],
            'neutral': [(13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20)],
            'sad': [(13, 19), (14, 19), (15, 19), (16, 19), (17, 19), (18, 19), (12, 20), (13, 20), (14, 20), (15, 20), (16, 20), (17, 20), (18, 20), (19, 20)]
        }

        time_coords = {
            'happy': [(30, 8), (29, 8), (29, 9), (29, 10), (30, 10), (30, 11), (30, 12), (29, 12), (27, 9), (26, 10), (27, 11)],  # LED pour <5
            'neutral': [(27, 8), (27, 9), (27, 10), (27, 11), (27, 12), (29, 8), (29, 9), (29, 10), (29, 11), (29, 12), (30, 8), (30, 12), (31, 8), (31, 9), (31, 10), (31, 11), (31, 12), (25, 9), (24, 10), (25, 11)],  # LED pour <10
            'sad': [(27, 8), (27, 9), (27, 10), (27, 11), (27, 12), (29, 8), (29, 9), (29, 10), (29, 11), (29, 12), (30, 8), (30, 12), (31, 8), (31, 9), (31, 10), (31, 11), (31, 12), (24, 9), (25, 10), (24, 11)],  # LED pour >10
        }

        mood_color = {
            'happy': 'GREEN_SMILEY',
            'neutral': 'YELLOW_SMILEY',
            'sad': 'RED_SMILEY'
        }

        self.set_pen(mood_color[mood])
        for x, y in smiley_coords:
            self.graphics.pixel(x, y)
        for x, y in eyes_coords:
            self.graphics.pixel(x, y)
        for x, y in mouth_coords[mood]:
            self.graphics.pixel(x, y)
        for x, y in time_coords[mood]:
            self.graphics.pixel(x, y)

        self.update()

    def play_bip(self, frequency):
        """Joue un bip sonore d'une fréquence donnée si le son est activé."""
        try:
            if self.sound_enabled:
                self.channel.play_tone(frequency, 0.3)  # Jouer une tonalité pour 0.3 seconde
                self.cu.play_synth()
                time.sleep(0.3)
                self.channel.trigger_release()  # Arrêter la tonalité
        except Exception as e:
            print(f"Erreur lors de la lecture du bip : {e}")

    def adjust_brightness(self):
        """Ajuste la luminosité en fonction des boutons de luminosité."""
        if self.cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_UP):
            if self.brightness < 1.0:
                self.brightness += 0.01
            print("Bouton ajustement luminosité pressé - augmentation de la luminosité")
        elif self.cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_DOWN):
            if self.brightness > 0.0:
                self.brightness -= 0.01
            print("Bouton ajustement luminosité pressé - réduction de la luminosité")
        self.cu.set_brightness(self.brightness)

    def adjust_volume(self):
        """Ajuste le volume en fonction des boutons de volume."""
        if self.cu.is_pressed(CosmicUnicorn.SWITCH_VOLUME_UP):
            if self.volume < 20000:  # Limite supérieure de la fréquence du son
                self.volume = min(self.volume + 10, 20000)
                self.channel.frequency(self.volume)
                print(f"Augmentation du volume. Fréquence actuelle : {self.volume} Hz")
        elif self.cu.is_pressed(CosmicUnicorn.SWITCH_VOLUME_DOWN):
            if self.volume > 10:  # Limite inférieure de la fréquence du son
                self.volume = max(self.volume - 10, 10)
                self.channel.frequency(self.volume)
                print(f"Diminution du volume. Fréquence actuelle : {self.volume} Hz")

    def display_digit(self, digit, col_start, row_start, color):
        """Affiche un chiffre à une position donnée sur l'écran."""
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
        self.set_pen(color)
        for dx, dy in digits[digit]:
            self.graphics.pixel(col_start + dx, row_start + dy)
        self.update()

    def display_clock(self, start_time, synced):
        """Affiche l'heure actuelle synchronisée ou calculée avec correction de fuseau horaire."""
        current_time = time.localtime(time.time() + 11 * 3600 if synced else start_time + 11 * 3600)
        hour = "{:02}".format(current_time[3])
        minute = "{:02}".format(current_time[4])
        second = current_time[5]
        self.display_digit(hour[0], 14, 1, 'WHITE')
        self.display_digit(hour[1], 18, 1, 'WHITE')
        if second % 2 == 0:
            self.graphics.pixel(22, 2)
            self.graphics.pixel(22, 4)
        else:
            self.set_pen('BLACK')
            self.graphics.pixel(22, 2)
            self.graphics.pixel(22, 4)
        self.display_digit(minute[0], 24, 1, 'WHITE')
        self.display_digit(minute[1], 28, 1, 'WHITE')
        self.update()

    def set_transition_variable(self, name):
        """Définit le texte à faire défiler."""
        self.transition_var = name
        self.scroll_shift = 0

    def display_message_frame_2(self, message):
        """Affiche un message au centre de l'écran."""
        PADDING = 2
        self.set_pen('BLACK')
        self.graphics.rectangle(0, 12, self.width, 12)
        self.set_pen('WHITE')

        lines = message.split('\n')
        y_offset = 12
        for line in lines:
            text_width = self.graphics.measure_text(line, 1)
            self.graphics.text(line, (self.width - text_width) // 2, y_offset, -1, 1)
            y_offset += 8
        self.update()

    def toggle_sound(self):
        """Active ou désactive le son et met à jour les LEDs en conséquence."""
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            print("Bouton A pressé - Activation du son")
            self.play_bip(500)
            self.update_led_sound_status(True)
        else:
            print("Bouton A pressé - Désactivation du son")
            self.play_bip(400)
            self.update_led_sound_status(False)

    def update_led_sound_status(self, sound_status=None):
        """Met à jour l'état des LEDs indépendamment de l'affichage du smiley."""
        if sound_status is None:
            sound_status = self.sound_enabled

        if sound_status:
            self.set_pen('BLUE')
            for x, y in self.led_positions_on:
                self.graphics.pixel(x, y)
        else:
            self.set_pen('BLUE')
            for x, y in self.led_positions_off_blue:
                self.graphics.pixel(x, y)
            self.set_pen('RED')
            for x, y in self.led_positions_off_red:
                self.graphics.pixel(x, y)
        self.update()

    def toggle_loop_pause(self):
        """Mets en pause/reprend la boucle d'affichage des agences et gère l'état de la LED."""
        self.loop_paused = not self.loop_paused
        if self.loop_paused:
            print("Bouton B pressé - Mise en pause de la boucle")
            self.set_pen('YELLOW')
            self.graphics.pixel(*self.pause_led_position)
            self.update()
        else:
            print("Bouton B pressé - Reprise de la boucle")
            self.set_pen('BLACK')
            self.graphics.pixel(*self.pause_led_position)
            self.update()

# Fonction pour arrêter proprement le script
def stop_script():
    print("Arrêt du script demandé...")
    display.clear()
    display.display_message_frame_2("KO\nREBOOT")
    display.update()
    time.sleep(2)
    raise SystemExit

# Fonction pour charger la clé API à partir d'un fichier .env
def load_api_key(file_path):
    """Charge la clé API depuis un fichier."""
    try:
        with open(file_path, "r") as f:
            for line in f:
                if line.startswith("API_KEY"):
                    api_key = line.strip().split('=')[1]
                    return api_key
    except OSError:
        print(f"Erreur : impossible de trouver ou lire le fichier {file_path}")
    return None

# Fonction pour se connecter au WiFi
def connect_wifi(ssid, password):
    """Tente de se connecter au réseau WiFi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    attempts = 0
    max_attempts = 5
    while not wlan.isconnected() and attempts < max_attempts:
        print(f"Connexion à {ssid}... Tentative {attempts + 1}/{max_attempts}")
        wlan.connect(ssid, password)
        time.sleep(5)  # Délai de 5 secondes pour tenter la connexion
        attempts += 1
    if wlan.isconnected():
        print(f"WiFi connecté avec l'IP : {wlan.ifconfig()[0]}")
        return True
    else:
        print("Échec de la connexion WiFi après plusieurs tentatives.")
        return False

# Fonction pour synchroniser l'heure avec NTP
def sync_time():
    """Tente de synchroniser l'heure avec des serveurs NTP."""
    ntp_servers = ['time.windows.com', 'ntp1.google.com', 'pool.ntp.org']
    for server in ntp_servers:
        try:
            ntptime.host = server
            ntptime.settime()
            print(f"Heure synchronisée via NTP avec {server}")
            return True
        except OSError as e:
            print(f"Erreur de synchronisation NTP avec {server}: {e}")
    print("Échec de la synchronisation NTP.")
    return False

# Fonction pour récupérer les données des agences via l'API
def get_agency_data(api_key):
    """Récupère les données des agences en appelant l'API."""
    url = "https://api.opt.nc/temps-attente-agences/csv"
    headers = {"x-apikey": api_key}
    try:
        response = requests.get(url, headers=headers)
        print(f"Appel API pour récupérer les données des agences, statut: {response.status_code}")
        if response.status_code == 200:
            print(f"Réponse API: {response.text}")  # Affiche le retour complet de l'API
            return parse_csv_data(response.content.decode('utf-8'))
        else:
            print(f"Erreur API : Statut {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de l'appel API : {e}")
    return None

# Fonction pour analyser le CSV des agences
def parse_csv_data(csv_content):
    """Analyse le fichier CSV des agences."""
    rows = csv_content.split("\n")
    data = [row.split(",") for row in rows[1:] if row.strip()]
    tableau_agences = []
    for row in data:
        agence_id = row[0].strip()
        designation = row[1].strip().replace("Agence de ", "").upper()
        realMaxWaitingTimeMs = int(row[2].strip())
        tableau_agences.append([agence_id, designation, realMaxWaitingTimeMs])
    return tableau_agences

# Fonction pour mettre à jour une seule agence avant l'affichage
def update_single_agency(api_key, agency):
    """Mise à jour d'une agence spécifique avant affichage."""
    agence_id, name, old_waiting_time = agency
    url = f"https://api.opt.nc/temps-attente-agences/temps-attente/agence/{agence_id}"
    headers = {"x-apikey": api_key}
    try:
        response = requests.get(url, headers=headers)
        print(f"Appel API pour agence {name} (ID: {agence_id}), statut: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse API agence {name}: {data}")  # Affiche le retour API pour l'agence
            new_waiting_time = data['realMaxWaitingTimeMs']
            agency[2] = new_waiting_time
            print(f"Temps d'attente mis à jour pour {name} (ID: {agence_id}) : {new_waiting_time // 60000} minutes (ancien {old_waiting_time // 60000} minutes)")
            return True
        else:
            print(f"Erreur API pour {name} (ID: {agence_id}) : {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour de l'agence {name} (ID: {agence_id}) : {e}")
    return False

# Fonction pour gérer la pression des boutons
def handle_button_press(cu):
    """Gère la pression du bouton A pour activer/désactiver le son, du bouton B pour mettre en pause, et du volume."""
    if cu.is_pressed(CosmicUnicorn.SWITCH_A):
        display.toggle_sound()  # Appelle la fonction toggle_sound
        return True  # Retourne True si le bouton est pressé
    if cu.is_pressed(CosmicUnicorn.SWITCH_B):
        display.toggle_loop_pause()  # Gère la mise en pause/reprise avec le bouton B
        return True
    # Ajuste le volume avec les boutons correspondants
    display.adjust_volume()
    return False

# Boucle principale pour afficher les agences
def main_loop(display, start_time, synced, api_key):
    """Boucle principale qui gère l'affichage des agences, le son, et le volume."""
    display.display_message_frame_2("INIT")
    time.sleep(2)

    if not sync_time():
        display.display_message_frame_2("NO NTP")
        time.sleep(5)
        return

    display.display_message_frame_2("WAIT")
    time.sleep(2)

    tableau_agences = get_agency_data(api_key)
    if not tableau_agences:
        display.display_message_frame_2("NO API")
        time.sleep(5)
        return

    current_index = 0
    while True:
        agence_id, name, waiting_time = tableau_agences[current_index]

        # Mise à jour des temps d'attente pour l'agence actuelle
        if update_single_agency(api_key, tableau_agences[current_index]):
            print(f"Agence mise à jour : {name}, Temps d'attente mis à jour.")
        else:
            print(f"Affichage des anciennes données pour : {name}")

        mood = 'happy' if waiting_time < 300000 else 'neutral' if waiting_time < 600000 else 'sad'
        display.clear()
        display.draw_frame(0, 6, 'YELLOW')
        display.draw_text_opt()
        display.draw_smiley(mood)
        display.set_transition_variable(name)

        print(f"Agence affichée : {name}, ID : {agence_id}, Temps d'attente : {waiting_time // 60000} minutes")

        for _ in range(100):
            display.scroll_text(display.transition_var)
            display.display_clock(start_time, synced)
            time.sleep(0.1)

            # Ajuste la luminosité et le volume en temps réel
            display.adjust_brightness()
            display.adjust_volume()

            # Gère la pression des boutons A et B
            handle_button_press(display.cu)

        # Gestion de la pause pour le bouton B
        if not display.loop_paused:
            current_index = (current_index + 1) % len(tableau_agences)

# Connexion Wi-Fi et lancement du script
wifi_connected = connect_wifi('TP-Link_F41E', '27611708')

if wifi_connected:
    # Initialisation de l'affichage
    display = CosmicUnicornDisplay()

    # Clé API
    api_key = load_api_key("api_key.env")

    # Lancer la boucle principale
    start_time = time.time()
    try:
        main_loop(display, start_time, wifi_connected, api_key)
    except KeyboardInterrupt:
        stop_script()
else:
    print("Impossible de démarrer le script sans connexion Wi-Fi.")

