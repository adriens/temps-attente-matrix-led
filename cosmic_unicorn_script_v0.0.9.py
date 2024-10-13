# Imports nécessaires pour les fonctionnalités utilisées dans le script.
import time  # Gestion du temps et des délais.
import network  # Module pour gérer la connexion réseau (Wi-Fi).
import ntptime  # Synchronisation du temps via NTP (Network Time Protocol).
import urequests as requests  # Pour effectuer des requêtes HTTP (comme des appels API).
import os  # Gestion des fichiers et des chemins.
import gc  # Gestion de la mémoire (garbage collector).
import _thread  # Gestion des threads (exécution parallèle).
import machine  # Pour interagir avec le matériel (comme les boutons, les LEDs).
from cosmic import CosmicUnicorn  # Import du module CosmicUnicorn pour gérer l'affichage sur l'appareil.
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN  # Gestion des graphiques pour l'affichage.

# Constantes pour définir les couleurs utilisées dans l'affichage, définies en RGB.
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

# Classe pour gérer l'affichage sur l'écran du Cosmic Unicorn.
class CosmicUnicornDisplay:
    def __init__(self):
        """Initialise l'affichage, les stylos, le statut du son, la luminosité et le volume."""
        self.cu = CosmicUnicorn()  	# Instance de CosmicUnicorn pour gérer l'affichage.
        self.graphics = PicoGraphics(display=DISPLAY_COSMIC_UNICORN)  # Instance pour gérer les graphiques.
        self.width, self.height = self.graphics.get_bounds()  # Récupère les dimensions de l'écran.
        self.pens = {color: self.graphics.create_pen(*rgb) for color, rgb in COLORS.items()}  # Crée des stylos pour les couleurs.
        self.scroll_shift = 0  # Variable de décalage pour le texte défilant.
        self.last_scroll_time = time.ticks_ms()  # Enregistre le dernier moment où le texte a défilé.
        self.transition_var = ''  # Variable pour stocker le texte défilant.
        self.graphics.set_font("bitmap4")  # Définit la police utilisée pour l'affichage du texte.
        self.sound_enabled = True  # Indique si le son est activé ou non.
        self.brightness = 0.5  # Définit la luminosité initiale de l'affichage.
        self.loop_paused = False  # Variable pour gérer la pause de la boucle d'affichage.
        self.volume = 500  # Fréquence initiale du bip sonore.
        self.pause_led_position = (1, 25)  # Position de la LED indiquant une pause.
        self.led_positions_on = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # Positions des LEDs quand le son est activé.
        self.led_positions_off_red = [(0, 9), (1, 10), (2, 11), (3, 12)]  # Positions des LEDs rouges quand le son est désactivé.
        self.led_positions_off_blue = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # Positions des LEDs bleues quand le son est désactivé.
        self.channel = self.cu.synth_channel(5)  # Canal sonore pour gérer les bips sonores.
        self.cu.set_brightness(self.brightness)  # Définit la luminosité initiale de l'écran.
        self.update_led_sound_status(self.sound_enabled)  # Met à jour les LEDs selon l'état du son.
        print("Affichage initialisé avec succès")  # Confirmation de l'initialisation réussie.

    def clear(self):
        """Efface l'écran sans toucher aux LEDs du son et de pause."""
        self.graphics.set_pen(self.pens['BLACK'])  # Définit la couleur du stylo à noir pour effacer.
        self.graphics.clear()  # Efface l'écran.
        self.update_led_sound_status(self.sound_enabled)  # Met à jour les LEDs du son.
        if self.loop_paused:  # Si la boucle est en pause, affiche la LED de pause.
            self.set_pen('YELLOW')
            self.graphics.pixel(*self.pause_led_position)
        self.update()  # Met à jour l'affichage.

    def update(self):
        """Met à jour l'affichage."""
        self.cu.update(self.graphics)  # Rafraîchit l'écran avec les nouvelles informations graphiques.

    def set_pen(self, color):
        """Définit la couleur du stylo graphique."""
        self.graphics.set_pen(self.pens[color])  # Définit le stylo à la couleur souhaitée.

    def scroll_text(self, message):
        """Gère le défilement du texte sur l'écran."""
        PADDING = 5  # Espace entre le texte et les bords de l'écran.
        STEP_TIME = 0.1  # Intervalle de temps entre chaque étape du défilement.
        msg_width = self.graphics.measure_text(message, 1)  # Mesure la largeur du texte.
        time_ms = time.ticks_ms()  # Récupère le temps actuel en millisecondes.

        # Si assez de temps s'est écoulé depuis la dernière étape du défilement.
        if time_ms - self.last_scroll_time > STEP_TIME * 1000:
            self.scroll_shift += 1  # Décale le texte vers la gauche.
            if self.scroll_shift >= msg_width + self.width + PADDING:  # Si le texte est entièrement défilé.
                self.scroll_shift = -self.width  # Réinitialise le décalage.
            self.last_scroll_time = time_ms  # Met à jour le dernier temps de défilement.

        # Efface la zone de texte.
        self.set_pen('BLACK')
        self.graphics.rectangle(0, 26, self.width, 6)  # Crée une zone de rectangle noire pour le texte.
        self.set_pen('WHITE')  # Définit le stylo à blanc pour le texte.
        self.graphics.text(message, PADDING - self.scroll_shift, 26, -1, 1)  # Affiche le texte défilant.
        self.update()  # Met à jour l'écran.

    def draw_frame(self, y_start, y_end, color):
        """Dessine un cadre autour du smiley."""
        self.set_pen(color)  # Définit le stylo à la couleur donnée.
        for x in range(0, self.width):  # Dessine les lignes horizontales en haut et en bas.
            self.graphics.pixel(x, y_start)
            self.graphics.pixel(x, y_end)
        for y in range(y_start, y_end + 1):  # Dessine les lignes verticales sur les côtés.
            self.graphics.pixel(0, y)
            self.graphics.pixel(self.width - 1, y)
        self.update()  # Met à jour l'affichage.

    def draw_text_opt(self):
        """Affiche le texte OPT NC sur la partie gauche de l'écran."""
        self.set_pen('BLUE')  # Définit le stylo à bleu.
        # Coordonnées des lettres O, P, et T pour former 'OPT'.
        o_coords = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 5), (3, 1), (3, 5), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)]
        p_coords = [(6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (7, 1), (7, 3), (8, 1), (8, 2), (8, 3)]
        t_coords = [(10, 1), (11, 1), (11, 2), (11, 3), (11, 4), (11, 5), (12, 1)]
        # Dessine chaque lettre en utilisant les coordonnées définies.
        for coords in [o_coords, p_coords, t_coords]:
            for x, y in coords:
                self.graphics.pixel(x, y)
        self.update()  # Met à jour l'affichage.

    def draw_smiley(self, mood):
        """Dessine un smiley en fonction de l'humeur (happy, neutral, sad) sans effacer les LEDs du son."""
        # Efface seulement la zone du smiley.
        self.set_pen('BLACK')
        self.graphics.rectangle(7, 7, 19, 19)  # Efface la zone où le smiley sera dessiné.

        # Coordonnées du smiley, des yeux, de la bouche et de la valeur d'attente en fonction de l'humeur (happy, neutral, sad).
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

        # Dessine le smiley.
        self.set_pen(mood_color[mood])
        for x, y in smiley_coords:
            self.graphics.pixel(x, y)
        for x, y in eyes_coords:
            self.graphics.pixel(x, y)
        for x, y in mouth_coords[mood]:
            self.graphics.pixel(x, y)
        for x, y in time_coords[mood]:
            self.graphics.pixel(x, y)

        self.update()  # Met à jour l'affichage
        
        # Ajouter la logique pour les bips
        if mood == 'neutral':  # 1 bip si humeur est neutre
            self.play_bip(self.volume)  # Joue un bip avec la fréquence actuelle
        elif mood == 'sad':  # 3 bips si humeur est triste
            for _ in range(3):
                self.play_bip(self.volume)  # Joue un bip avec la fréquence actuelle
                time.sleep(0.3)  # Pause entre les bips

    def play_bip(self, frequency):
        """Joue un bip sonore d'une fréquence donnée si le son est activé."""
        try:
            if self.sound_enabled:  # Si le son est activé.
                self.channel.play_tone(frequency, 0.3)  # Joue une tonalité pendant 0.3 seconde.
                self.cu.play_synth()  # Joue le son sur le canal synthétique.
                time.sleep(0.3)  # Attend que le son soit joué.
                self.channel.trigger_release()  # Arrête le son.
        except Exception as e:
            print(f"Erreur lors de la lecture du bip : {e}")  # Capture toute erreur et l'affiche.

    def adjust_brightness(self):
        """Ajuste la luminosité en fonction des boutons de luminosité."""
        if self.cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_UP):  # Si le bouton pour augmenter la luminosité est pressé.
            if self.brightness < 1.0:  # Limite supérieure pour la luminosité.
                self.brightness += 0.01  # Augmente la luminosité.
            print("Bouton ajustement luminosité pressé - augmentation de la luminosité")
        elif self.cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_DOWN):  # Si le bouton pour diminuer la luminosité est pressé.
            if self.brightness > 0.0:  # Limite inférieure pour la luminosité.
                self.brightness -= 0.01  # Diminue la luminosité.
            print("Bouton ajustement luminosité pressé - réduction de la luminosité")
        self.cu.set_brightness(self.brightness)  # Applique la nouvelle luminosité.

    def adjust_volume(self):
        """Ajuste le volume en fonction des boutons de volume."""
        if self.cu.is_pressed(CosmicUnicorn.SWITCH_VOLUME_UP):  # Si le bouton pour augmenter le volume est pressé.
            if self.volume < 20000:  # Limite supérieure pour la fréquence sonore.
                self.volume = min(self.volume + 10, 20000)  # Augmente la fréquence (volume).
                self.channel.frequency(self.volume)  # Applique la nouvelle fréquence au canal sonore.
                print(f"Augmentation du volume. Fréquence actuelle : {self.volume} Hz")
        elif self.cu.is_pressed(CosmicUnicorn.SWITCH_VOLUME_DOWN):  # Si le bouton pour diminuer le volume est pressé.
            if self.volume > 10:  # Limite inférieure pour la fréquence sonore.
                self.volume = max(self.volume - 10, 10)  # Diminue la fréquence (volume).
                self.channel.frequency(self.volume)  # Applique la nouvelle fréquence au canal sonore.
                print(f"Diminution du volume. Fréquence actuelle : {self.volume} Hz")

    # Fonction pour afficher l'heure sous forme de chiffres à l'écran.
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
        self.set_pen(color)  # Définit le stylo à la couleur donnée.
        for dx, dy in digits[digit]:  # Parcourt les coordonnées du chiffre et les affiche.
            self.graphics.pixel(col_start + dx, row_start + dy)
        self.update()  # Met à jour l'affichage.

    # Fonction pour afficher l'horloge sur l'écran.
    def display_clock(self, start_time, synced):
        """Affiche l'heure actuelle synchronisée ou calculée avec correction de fuseau horaire."""
        current_time = time.localtime(time.time() + 11 * 3600 if synced else start_time + 11 * 3600)
        hour = "{:02}".format(current_time[3])  # Récupère l'heure actuelle (HH).
        minute = "{:02}".format(current_time[4])  # Récupère les minutes actuelles (MM).
        second = current_time[5]  # Récupère les secondes actuelles (SS).
        self.display_digit(hour[0], 14, 1, 'WHITE')  # Affiche le premier chiffre des heures.
        self.display_digit(hour[1], 18, 1, 'WHITE')  # Affiche le deuxième chiffre des heures.
        if second % 2 == 0:  # Si les secondes sont paires, affiche les deux points de séparation.
            self.graphics.pixel(22, 2)
            self.graphics.pixel(22, 4)
        else:  # Sinon, les efface.
            self.set_pen('BLACK')
            self.graphics.pixel(22, 2)
            self.graphics.pixel(22, 4)
        self.display_digit(minute[0], 24, 1, 'WHITE')  # Affiche le premier chiffre des minutes.
        self.display_digit(minute[1], 28, 1, 'WHITE')  # Affiche le deuxième chiffre des minutes.
        self.update()  # Met à jour l'affichage.

    def set_transition_variable(self, name):
        """Définit le texte à faire défiler."""
        self.transition_var = name  # Définit la variable de transition avec le texte à afficher.
        self.scroll_shift = 0  # Réinitialise le décalage du texte.

    def display_message_frame_2(self, message):
        """Affiche un message au centre de l'écran."""
        PADDING = 2  # Espacement pour centrer le texte.
        self.set_pen('BLACK')  # Efface la zone centrale.
        self.graphics.rectangle(0, 12, self.width, 12)
        self.set_pen('WHITE')  # Définit le stylo à blanc.

        lines = message.split('\n')  # Sépare le message en plusieurs lignes si nécessaire.
        y_offset = 12  # Départ de l'affichage.
        for line in lines:  # Pour chaque ligne du message.
            text_width = self.graphics.measure_text(line, 1)  # Mesure la longueur du texte.
            self.graphics.text(line, (self.width - text_width) // 2, y_offset, -1, 1)  # Centre le texte.
            y_offset += 8  # Passe à la ligne suivante.
        self.update()  # Met à jour l'affichage.

    # Fonction pour activer ou désactiver le son et mettre à jour les LEDs correspondantes.
    def toggle_sound(self):
        """Active ou désactive le son et met à jour les LEDs en conséquence."""
        self.sound_enabled = not self.sound_enabled  # Inverse l'état du son.
        if self.sound_enabled:
            print("Bouton A pressé - Activation du son")
            self.play_bip(500)  # Joue un bip à une certaine fréquence.
            self.update_led_sound_status(True)  # Met à jour les LEDs pour indiquer que le son est activé.
        else:
            print("Bouton A pressé - Désactivation du son")
            self.play_bip(400)  # Joue un bip différent pour indiquer la désactivation du son.
            self.update_led_sound_status(False)  # Met à jour les LEDs pour indiquer que le son est désactivé.

    # Fonction pour mettre à jour les LEDs en fonction de l'état du son (activé ou désactivé).
    def update_led_sound_status(self, sound_status=None):
        """Met à jour l'état des LEDs indépendamment de l'affichage du smiley."""
        if sound_status is None:  # Si aucun état de son n'est passé, utilise celui par défaut.
            sound_status = self.sound_enabled

        if sound_status:  # Si le son est activé, allume les LEDs bleues.
            self.set_pen('BLUE')
            for x, y in self.led_positions_on:
                self.graphics.pixel(x, y)
        else:  # Si le son est désactivé, allume les LEDs rouges.
            self.set_pen('BLUE')
            for x, y in self.led_positions_off_blue:
                self.graphics.pixel(x, y)
            self.set_pen('RED')
            for x, y in self.led_positions_off_red:
                self.graphics.pixel(x, y)
        self.update()  # Met à jour l'affichage.

    # Fonction pour mettre en pause ou reprendre la boucle d'affichage des agences.
    def toggle_loop_pause(self):
        """Mets en pause/reprend la boucle d'affichage des agences et gère l'état de la LED."""
        self.loop_paused = not self.loop_paused  # Inverse l'état de la pause.
        if self.loop_paused:  # Si la boucle est en pause.
            print("Bouton B pressé - Mise en pause de la boucle")
            self.set_pen('YELLOW')  # Allume la LED de pause.
            self.graphics.pixel(*self.pause_led_position)
            self.update()
        else:  # Si la boucle reprend.
            print("Bouton B pressé - Reprise de la boucle")
            self.set_pen('BLACK')  # Éteint la LED de pause.
            self.graphics.pixel(*self.pause_led_position)
            self.update()

# Fonction pour supprimer les accents : définit sur é et è
def normalize_name(text):
    """Remplace manuellement les accents par leurs équivalents non accentués et met le texte en majuscules."""
    accents = {
        'è': 'e', 'é': 'e',
    }
    # Remplacer chaque caractère accentué par son équivalent non accentué
    return ''.join(accents.get(c, c) for c in text).upper()

# Fonction pour arrêter proprement le script.
def stop_script():
    """Arrête proprement le script."""
    print("Arrêt du script demandé...")
    display.clear()  # Efface l'écran.
    display.display_message_frame_2("KO\nREBOOT")  # Affiche un message de redémarrage.
    display.update()  # Met à jour l'affichage.
    time.sleep(2)  # Pause de 2 secondes avant l'arrêt.
    raise SystemExit  # Arrête le script.

# Fonction pour charger la clé API depuis un fichier.
def load_api_key(file_path):
    """Charge la clé API depuis un fichier."""
    try:
        with open(file_path, "r") as f:  # Ouvre le fichier contenant la clé API.
            for line in f:
                if line.startswith("API_KEY"):  # Cherche la ligne contenant la clé API.
                    api_key = line.strip().split('=')[1]  # Extrait la clé API.
                    return api_key
    except OSError:
        print(f"Erreur : impossible de trouver ou lire le fichier {file_path}")
    return None  # Si erreur, retourne None.

# Fonction pour se connecter au WiFi
def connect_wifi(ssid, password):
    """Tente de se connecter au réseau WiFi avec un maximum de 5 tentatives."""
    wlan = network.WLAN(network.STA_IF)  # Initialise l'interface WiFi en mode station (client)
    wlan.active(True)  # Active l'interface WiFi
    attempts = 0  # Initialise le compteur de tentatives
    max_attempts = 5  # Nombre maximal de tentatives de connexion
    while not wlan.isconnected() and attempts < max_attempts:  # Boucle jusqu'à ce que le WiFi soit connecté ou que le nombre maximal de tentatives soit atteint
        print(f"Connexion à {ssid}... Tentative {attempts + 1}/{max_attempts}")
        wlan.connect(ssid, password)  # Lance la connexion au réseau WiFi avec les informations fournies
        time.sleep(5)  # Attend 5 secondes entre les tentatives
        attempts += 1  # Incrémente le nombre de tentatives
    if wlan.isconnected():  # Vérifie si la connexion a réussi
        print(f"WiFi connecté avec l'IP : {wlan.ifconfig()[0]}")  # Affiche l'adresse IP si la connexion a réussi
        return True  # Retourne True si la connexion est établie
    else:
        print("Échec de la connexion WiFi après plusieurs tentatives.")  # Affiche un message d'erreur si la connexion échoue
        return False  # Retourne False si la connexion n'a pas pu être établie

# Fonction pour synchroniser l'heure avec un serveur NTP
def sync_time():
    """Synchronise l'heure locale avec un serveur NTP."""
    ntp_servers = ['time.windows.com', 'ntp1.google.com', 'pool.ntp.org']  # Liste des serveurs NTP à contacter
    for server in ntp_servers:  # Parcourt chaque serveur NTP
        try:
            ntptime.host = server  # Définit le serveur NTP à contacter
            ntptime.settime()  # Tente de synchroniser l'heure
            print(f"Heure synchronisée via NTP avec {server}")  # Affiche un message si la synchronisation réussit
            return True  # Retourne True si la synchronisation est réussie
        except OSError as e:
            print(f"Erreur de synchronisation NTP avec {server}: {e}")  # Affiche une erreur si la synchronisation échoue
    print("Échec de la synchronisation NTP.")  # Affiche un message si aucun serveur NTP n'a pu être contacté
    return False  # Retourne False si la synchronisation échoue

# Fonction pour récupérer les données des agences via l'API
def get_agency_data(api_key):
    """Récupère les données des agences en utilisant l'API avec la clé fournie."""
    url = "https://api.opt.nc/temps-attente-agences/csv"  # URL de l'API qui fournit les données des agences
    headers = {"x-apikey": api_key}  # Ajoute l'API Key aux en-têtes HTTP pour l'authentification
    try:
        response = requests.get(url, headers=headers)  # Effectue une requête GET à l'API
        print(f"Appel API pour récupérer les données des agences, statut: {response.status_code}")  # Affiche le code de statut HTTP de la réponse
        if response.status_code == 200:  # Si la requête réussit
            print(f"Réponse API: {response.text}")  # Affiche la réponse de l'API
            return parse_csv_data(response.content.decode('utf-8'))  # Analyse les données CSV de l'API
        else:
            print(f"Erreur API : Statut {response.status_code}")  # Affiche un message d'erreur si la requête échoue
    except Exception as e:
        print(f"Erreur lors de l'appel API : {e}")  # Affiche une erreur si une exception est levée
    return None  # Retourne None si les données n'ont pas pu être récupérées

# Fonction pour analyser le CSV des agences
def parse_csv_data(csv_content):
    """Analyse les données CSV des agences et les convertit en tableau exploitable."""
    rows = csv_content.split("\n")  # Divise le contenu du fichier CSV en lignes
    data = [row.split(",") for row in rows[1:] if row.strip()]  # Divise chaque ligne en colonnes (par virgules) et ignore les lignes vides
    tableau_agences = []  # Liste pour stocker les données des agences
    for row in data:  # Parcourt chaque ligne de données
        agence_id = row[0].strip()  # Récupère l'ID de l'agence
        designation = normalize_name(row[1].strip().replace("Agence de ", "").upper())  # Récupère et normalise le nom de l'agence
        realMaxWaitingTimeMs = int(row[2].strip())  # Convertit le temps d'attente maximum en entier
        tableau_agences.append([agence_id, designation, realMaxWaitingTimeMs])  # Ajoute l'agence à la liste
    return tableau_agences  # Retourne la liste des agences

# Fonction pour mettre à jour une seule agence avant l'affichage
def update_single_agency(api_key, agency):
    """Met à jour les données d'une agence spécifique en appelant l'API."""
    agence_id, name, old_waiting_time = agency  # Récupère les informations actuelles de l'agence
    url = f"https://api.opt.nc/temps-attente-agences/temps-attente/agence/{agence_id}"  # Construit l'URL de l'API pour l'agence spécifique
    headers = {"x-apikey": api_key}  # Ajoute l'API Key aux en-têtes HTTP
    try:
        response = requests.get(url, headers=headers)  # Effectue une requête GET pour récupérer les nouvelles données de l'agence
        print(f"Appel API pour agence {name} (ID: {agence_id}), statut: {response.status_code}")  # Affiche le statut de la réponse API
        if response.status_code == 200:  # Si la requête réussit
            data = response.json()  # Convertit la réponse en format JSON
            print(f"Réponse API agence {name}: {data}")  # Affiche les nouvelles données de l'agence
            new_waiting_time = data['realMaxWaitingTimeMs']  # Récupère le temps d'attente mis à jour
            agency[2] = new_waiting_time  # Met à jour le temps d'attente dans la liste des agences
            print(f"Temps d'attente mis à jour pour {name} (ID: {agence_id}) : {new_waiting_time // 60000} minutes (ancien {old_waiting_time // 60000} minutes)")
            return True  # Retourne True si la mise à jour a réussi
        else:
            print(f"Erreur API pour {name} (ID: {agence_id}) : {response.status_code}")  # Affiche un message d'erreur en cas d'échec
    except Exception as e:
        print(f"Erreur lors de la mise à jour de l'agence {name} (ID: {agence_id}) : {e}")  # Affiche une erreur en cas d'exception
    return False  # Retourne False si la mise à jour a échoué

# Fonction pour gérer la pression des boutons
def handle_button_press(cu):
    """Gère les pressions des boutons A et B et ajuste le volume."""
    if cu.is_pressed(CosmicUnicorn.SWITCH_A):  # Si le bouton A est pressé
        display.toggle_sound()  # Active ou désactive le son
        return True  # Retourne True pour indiquer que le bouton a été pressé
    if cu.is_pressed(CosmicUnicorn.SWITCH_B):  # Si le bouton B est pressé
        display.toggle_loop_pause()  # Met en pause ou reprend la boucle d'affichage des agences
        return True
    display.adjust_volume()  # Ajuste le volume avec les boutons de volume
    return False  # Retourne False si aucun bouton n'a été pressé

# Boucle principale pour afficher les agences
def main_loop(display, start_time, synced, api_key):
    """Boucle principale qui gère l'affichage des agences, le son, et le volume."""
    display.display_message_frame_2("INIT")  # Affiche le message "INIT" à l'écran
    time.sleep(2)  # Attend 2 secondes

    if not sync_time():  # Si la synchronisation NTP échoue
        display.display_message_frame_2("NO NTP")  # Affiche "NO NTP" pour indiquer l'échec de la synchronisation
        time.sleep(5)  # Attend 5 secondes avant de quitter
        return

    display.display_message_frame_2("WAIT")  # Affiche "WAIT" pendant que les données sont récupérées
    time.sleep(2)  # Attend 2 secondes

    tableau_agences = get_agency_data(api_key)  # Récupère les données des agences via l'API
    if not tableau_agences:  # Si aucune donnée n'est récupérée
        display.display_message_frame_2("NO API")  # Affiche "NO API" en cas d'erreur d'API
        time.sleep(5)  # Attend 5 secondes avant de quitter
        return

    current_index = 0  # Initialise l'index de l'agence à afficher
    while True:  # Boucle infinie pour afficher les agences
        agence_id, name, waiting_time = tableau_agences[current_index]  # Récupère les informations de l'agence actuelle

        # Met à jour les données de l'agence actuelle
        if update_single_agency(api_key, tableau_agences[current_index]):
            print(f"Agence mise à jour : {name}, Temps d'attente mis à jour.")  # Affiche un message de succès
        else:
            print(f"Affichage des anciennes données pour : {name}")  # Affiche un message si la mise à jour échoue

        # Détermine l'humeur (happy, neutral, sad) en fonction du temps d'attente
        mood = 'happy' if waiting_time < 300000 else 'neutral' if waiting_time < 600000 else 'sad'
        display.clear()  # Efface l'écran
        display.draw_frame(0, 6, 'YELLOW')  # Dessine un cadre autour du smiley
        display.draw_text_opt()  # Affiche le texte "OPT NC"
        display.draw_smiley(mood)  # Affiche le smiley correspondant à l'humeur
        display.set_transition_variable(name)  # Définit le nom de l'agence à faire défiler

        print(f"Agence affichée : {name}, ID : {agence_id}, Temps d'attente : {waiting_time // 60000} minutes")

        for _ in range(100):  # Boucle pour gérer le défilement du texte et afficher l'heure
            display.scroll_text(display.transition_var)  # Fait défiler le nom de l'agence
            display.display_clock(start_time, synced)  # Affiche l'heure
            time.sleep(0.1)  # Pause de 100 ms entre les itérations

            # Ajuste la luminosité et le volume en temps réel
            display.adjust_brightness()
            display.adjust_volume()

            # Gère la pression des boutons A et B
            handle_button_press(display.cu)

        # Passe à l'agence suivante si la boucle n'est pas en pause
        if not display.loop_paused:
            current_index = (current_index + 1) % len(tableau_agences)  # Incrémente l'index et revient à 0 après la dernière agence

# Connexion Wi-Fi et lancement du script
wifi_connected = connect_wifi('TP-Link_F41E', '27611708')  # Se connecte au WiFi

if wifi_connected:
    # Si la connexion WiFi est réussie, initialise l'affichage
    display = CosmicUnicornDisplay()

    # Charge la clé API depuis le fichier
    api_key = load_api_key("api_key.env")

    # Lancer la boucle principale
    start_time = time.time()  # Récupère l'heure actuelle au démarrage
    try:
        main_loop(display, start_time, wifi_connected, api_key)  # Démarre la boucle principale
    except KeyboardInterrupt:
        stop_script()  # Arrête proprement le script si une interruption clavier (Ctrl+C) est détectée
else:
    print("Impossible de démarrer le script sans connexion Wi-Fi.")  # Affiche un message si la connexion WiFi échoue


