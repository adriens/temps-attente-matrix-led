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

# Initialiser attempts pour le suivi des tentatives de connexion WiFi
attempts = 0

# Constantes pour définir les couleurs utilisées dans l'affichage, définies en RGB.
COLORS = {
    'YELLOW': (251, 189, 8),
    'WHITE': (255, 255, 255),
    'BLUE': (40, 44, 131),
    'GREEN': (0, 255, 0),
    'BLACK': (0, 0, 0),
    'RED': (255, 0, 0),
    'PINK': (255, 105, 180),
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
        self.led_positions_off_red = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # Positions des LEDs rouges quand le son est désactivé.
        self.led_positions_off_blue = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # Positions des LEDs bleues quand le son est désactivé.
        self.led_positions_wifi_ko = [(0, 17), (1, 16), (1, 17), (1, 18), (2, 15), (2, 16), (2, 17), (2, 18), (2, 19)]
        self.channel = self.cu.synth_channel(5)  # Canal sonore pour gérer les bips sonores.
        self.cu.set_brightness(self.brightness)  # Définit la luminosité initiale de l'écran.
        self.display_mode = 0  # Variable pour suivre le mode d'affichage
        self.update_led_sound_status(self.sound_enabled)  # Met à jour les LEDs selon l'état du son.
        print("Affichage initialisé avec succès")  # Confirmation de l'initialisation réussie.

    def clear(self):
        """Efface l'écran sans toucher aux LEDs du son et de pause."""
        self.graphics.set_pen(self.pens['BLACK'])  # Définit la couleur du stylo à noir pour effacer.
        self.graphics.clear()  # Efface l'écran.
        self.update_led_sound_status(self.sound_enabled)  # Met à jour les LEDs du son.
        self.update_led_wifi_status(self.check_wifi_status(network.WLAN(network.STA_IF)))  # Maintient l'état des LEDs WiFi
        if self.loop_paused:  # Si la boucle est en pause, affiche la LED de pause.
            self.set_pen('YELLOW')
            self.graphics.pixel(*self.pause_led_position)
        self.update()  # Met à jour l'affichage.

    def update(self):
        """Met à jour l'affichage."""
        self.cu.update(self.graphics)  # Rafraîchit l'écran avec les nouvelles informations graphiques.

    def set_pen(self, color):
        """Définit la couleur du stylo graphique."""
        if color in self.pens:
            self.graphics.set_pen(self.pens[color])  # Définit le stylo à la couleur souhaitée.
        else:
            print(f"Erreur : La couleur {color} n'est pas définie.")
    
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
            '4': [(0, 0), (0, 1), (0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
            '5': [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (1, 4), (0, 4)],
            '6': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (2, 3), (2, 2), (1, 2)],
            '7': [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (1, 2)],
            '8': [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2), (0, 3), (2, 3), (0, 4), (1, 4), (2, 4)],
            '9': [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (1, 4), (0, 4)]
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
        """Met à jour l'état des LEDs indépendamment de l'affichage du smiley, uniquement pendant l'affichage des agences."""
        if sound_status is None:
            sound_status = self.sound_enabled

        if self.display_mode == 3:  # Mettre à jour les LEDs uniquement dans le mode agence (mode 3)
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
            
    def update_led_wifi_status(self, wifi_status):
        """Met à jour l'état des LEDs en fonction de l'état du WiFi."""
        if wifi_status:  # Si le WiFi est connecté, éteindre les LEDs rouges.
            self.set_pen('BLACK')
            for x, y in self.led_positions_wifi_ko:
                self.graphics.pixel(x, y)
        else:  # Si le WiFi est déconnecté, allumer les LEDs rouges et les maintenir allumées.
            self.set_pen('RED')
            for x, y in self.led_positions_wifi_ko:
                self.graphics.pixel(x, y)
        self.update()  # Met à jour l'affichage pour appliquer les changements
    
    def check_wifi_status(self, wlan):
        """Vérifie l'état de la connexion WiFi, met à jour l'affichage LED et arrête le script si nécessaire."""
        global attempts
        if wlan.isconnected():
            print("WIFI OK")
            attempts = 0  # Réinitialiser le compteur d'échecs
            return True
        else:
            print("WIFI KO")
            attempts += 1  # Incrémenter la variable d'échecs
    
            # Émission d'un bip pour signaler la perte de connexion
            self.play_bip(1000)  # Bip sonore pour signaler l'échec de connexion
    
            # Si la variable attempts dépasse 5, déclencher l'arrêt du script
            if attempts > 10:
                stop_script(self, wifi_issue=True)  # Spécifie que l'arrêt est dû à un problème de WiFi
            return False

# Matrices pour les lettres avec une largeur de 3 LED et une hauteur de 5 LED
LETTER_MAP_3 = {
    'C': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0), (2, 4), (1, 4)],
    'L': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4)],
    'E': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 4), (2, 0), (2, 4)],
    'W': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 3), (2, 2), (2, 0), (2, 1), (2, 3), (2, 4)],
    'I': [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2), (1, 3), (1, 4), (0, 4), (2, 4)],
    'F': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (2, 0)],
    'A': [(1, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2), (0, 3), (2, 3), (0, 4), (2, 4)],
    'P': [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2), (0, 3), (0, 4)],
    'O': [(1, 0), (0, 1), (2, 1), (0, 2), (2, 2), (0, 3), (2, 3), (1, 4)],
    'K': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (2, 0), (1, 2), (2, 4)],
    'S': [(0, 1), (0, 2), (1, 0), (2, 0), (1, 2), (2, 3), (0, 4), (1, 4)],
    'U': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (1, 4)],
    'N': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (1, 1), (1, 2)],
    'D': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 1), (2, 2), (2, 3), (1, 4)],
    'R': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0), (1, 2), (2, 2), (1, 3), (2, 4)],
    'G': [(1, 0), (0, 1), (2, 1), (0, 2), (2, 2), (0, 3), (2, 3), (1, 4), (2, 4)],
    'Y': [(0, 0), (2, 0), (1, 1), (1, 2), (1, 3), (1, 4)],
    'T': [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2), (1, 3), (1, 4)],
    'H': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
    'V': [(0, 0), (0, 1), (0, 2), (1, 3), (2, 0), (2, 1), (2, 2)],
    'M': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
    'X': [(0, 0), (0, 1), (0, 3), (0, 4), (2, 0), (2, 1), (2, 3), (2, 4), (1, 2)],

}

# Matrices pour les lettres avec une largeur de 4 LED et une hauteur de 5 LED
LETTER_MAP_4 = {
    'C': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 4), (2, 0), (2, 4), (3, 0), (3, 4)],
    'L': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4), (2, 4), (3, 4)],
    'E': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 4), (2, 0), (2, 2), (2, 4), (3, 0), (3, 4)],
    'W': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 3), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4)],
    'I': [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
    'F': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0)],
    'A': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4)],
    'P': [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (0, 3), (0, 4)],
    'O': [(1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (0, 3), (3, 3), (1, 4), (2, 4)],
    'K': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (3, 0), (1, 2), (2, 1), (2, 3), (3, 4)],
    'N': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 2), (2, 3), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4)],
    'R': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (2, 2), (1, 2), (2, 3), (3, 4)],
    'B': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0), (3, 1), (2, 2), (1, 2), (3, 3), (3, 4), (2, 4), (1, 4)],
    'T': [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (1, 2), (2, 2), (1, 3), (2, 3), (1, 4), (2, 4)],
    'S': [(3, 0), (2, 0), (1, 0), (0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2), (3, 3), (3, 4), (2, 4), (1, 4), (0, 4)],
    'D': [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0), (3, 1), (3, 2), (3, 3), (2, 4), (1, 4), (0, 4)],
}

def loading_animation_step(display, step):
    """Affiche progressivement l'animation de chargement sur l'écran en fonction de l'étape."""
    blocks = [
        [(0, 30), (0, 31), (0, 32), (1, 30), (1, 31), (1, 32), (2, 30), (2, 31), (2, 32)],
        [(3, 30), (3, 31), (3, 32), (4, 30), (4, 31), (4, 32), (5, 30), (5, 31), (5, 32)],
        [(6, 30), (6, 31), (6, 32), (7, 30), (7, 31), (7, 32), (8, 30), (8, 31), (8, 32)],
        [(9, 30), (9, 31), (9, 32), (10, 30), (10, 31), (10, 32), (11, 30), (11, 31), (11, 32)],
        [(12, 30), (12, 31), (12, 32), (13, 30), (13, 31), (13, 32), (14, 30), (14, 31), (14, 32)],
        [(15, 30), (15, 31), (15, 32), (16, 30), (16, 31), (16, 32), (17, 30), (17, 31), (17, 32)],
        [(18, 30), (18, 31), (18, 32), (19, 30), (19, 31), (19, 32), (20, 30), (20, 31), (20, 32)],
        [(21, 30), (21, 31), (21, 32), (22, 30), (22, 31), (22, 32), (23, 30), (23, 31), (23, 32)],
        [(24, 30), (24, 31), (24, 32), (25, 30), (25, 31), (25, 32), (26, 30), (26, 31), (26, 32)],
        [(27, 30), (27, 31), (27, 32), (28, 30), (28, 31), (28, 32), (29, 30), (29, 31), (29, 32)],
        [(30, 30), (30, 31), (30, 32), (31, 30), (31, 31), (31, 32)]
    ]

    if step < len(blocks):
        # Vérifie si la couleur 'WHITE' est définie
        if 'WHITE' in display.pens:
            display.set_pen('WHITE')
        else:
            print("Erreur : La couleur 'WHITE' n'est pas définie.")
            return

        # Dessine le bloc de LEDs pour l'étape en cours
        for x, y in blocks[step]:
            display.graphics.pixel(x, y)
        display.update()
        
def exploding_heart_animation(display):
    """Crée une animation d'un cœur explosant à partir d'une LED centrale, qui disparaît ensuite."""
    # Définir la LED centrale de départ
    center_led = (15, 15)
    
    # Liste des positions des LEDs formant le cœur final
    heart_positions = [
        (15, 12), (14, 11), (16, 11), (13, 10), (17, 10), 
        (12, 9), (11, 9), (10, 9), (18, 9), (19, 9), (20, 9), 
        (9, 10), (21, 10), (8, 11), (22, 11), (7, 12), (7, 13), 
        (7, 14), (23, 12), (23, 13), (23, 14), (8, 15), (22, 15), 
        (9, 16), (21, 16), (10, 17), (20, 17), (11, 18), (19, 18), 
        (12, 19), (18, 19), (13, 20), (17, 20), (14, 21), (16, 21), (15, 22)
    ]
    
    # Afficher la LED centrale
    display.set_pen('PINK')
    display.graphics.pixel(*center_led)
    display.update()
    time.sleep(0.2)  # Petite pause pour rendre l'animation visible

    # Ajouter les LEDs petit à petit jusqu'à former le cœur final
    for i, led in enumerate(heart_positions):
        # Lorsque la moitié des LEDs sont allumées, éteindre la LED centrale
        if i == len(heart_positions) // 2:
            display.set_pen('BLACK')
            display.graphics.pixel(*center_led)

        # Afficher la LED courante du cœur
        display.set_pen('PINK')
        display.graphics.pixel(*led)
        display.update()
        time.sleep(0.05)  # Pause pour rendre l'animation progressive

# Fonction d'affichage de l'écran d'accueil
def display_welcome_screen(display):
    """Affiche l'écran d'accueil initial avec les pixels identifiés pour chaque lettre de 'UNC OPT'."""
    display.clear()  # Efface l'écran pour afficher uniquement le message d'accueil
    exploding_heart_animation(display)  # Lancer l'animation du cœur explosant

    # Coordonnées pour chaque caractère
    coords = {
        'U': [(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (6, 5), (6, 4), (6, 3), (6, 2), (6, 1)],
        'N': [(8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (9, 2), (10, 3), (10, 4), (11, 5), (12, 6), (12, 5), (12, 4), (12, 3), (12, 2), (12, 1)],
        'C': [(14, 1), (14, 2), (14, 3), (14, 4), (14, 5), (14, 6), (15, 1), (16, 1), (17, 1), (18, 1), (15, 6), (16, 6), (17, 6), (18, 6)],
        'O': [(14, 25), (14, 26), (14, 27), (14, 28), (14, 29), (14, 30), (15, 30), (16, 30), (17, 30), (18, 25), (18, 26), (18, 27), (18, 28), (18, 29), (18, 30), (15, 25), (16, 25), (17, 25)],
        'P': [(20, 25), (20, 26), (20, 27), (20, 28), (20, 29), (20, 30), (21, 25), (22, 25), (23, 25), (24, 25), (24, 26), (24, 27), (23, 27), (22, 27), (21, 27)],
        'T': [(26, 25), (27, 25), (28, 25), (29, 25), (30, 25), (28, 26), (28, 27), (28, 28), (28, 29), (28, 30)]
    }

    # Définir les couleurs pour chaque partie du message
    colors = {
        'U': 'BLUE',
        'N': 'BLUE',
        'C': 'BLUE',
        'O': 'YELLOW_SMILEY',
        'P': 'YELLOW_SMILEY',
        'T': 'YELLOW_SMILEY',
    }

    # Afficher chaque caractère avec sa couleur
    for char, pixels in coords.items():
        display.set_pen(colors[char])  # Choisit la couleur définie pour le caractère
        for x, y in pixels:
            display.graphics.pixel(x, y)  # Allume chaque pixel correspondant

    display.update()  # Met à jour l'affichage avec le message complet

# Fonction pour dessiner une lettre de la map 3 spécifique à une position donnée
def draw_letter_3(graphics, letter, x, y, pen):
    if letter in LETTER_MAP_3:
        graphics.set_pen(pen)
        for dx, dy in LETTER_MAP_3[letter]:
            graphics.pixel(x + dx, y + dy)


# Fonction pour dessiner un mot entier en map 3
def draw_word_3(graphics, word, x, y, pen, spacing=4):
    current_x = x
    for letter in word:
        draw_letter_3(graphics, letter, current_x, y, pen)
        current_x += spacing

# Fonction pour dessiner une lettre de la map 4 spécifique à une position donnée
def draw_letter_4(graphics, letter, x, y, pen):
    if letter in LETTER_MAP_4:
        graphics.set_pen(pen)
        for dx, dy in LETTER_MAP_4[letter]:
            graphics.pixel(x + dx, y + dy)


# Fonction pour dessiner un mot entier en map 4
def draw_word_4(graphics, word, x, y, pen, spacing=5):
    """Dessine un mot entier en utilisant la lettre de taille 4 LED de largeur et 5 LED de hauteur."""
    current_x = x
    for letter in word:
        if letter in LETTER_MAP_4:
            graphics.set_pen(pen)
            for dx, dy in LETTER_MAP_4[letter]:
                graphics.pixel(current_x + dx, y + dy)
            current_x += spacing  # Espacement entre les lettres


# Fonction d'affichage de l'écran d'accueil
def display_info_screen(self, wifi_status, api_key_status):
    """Affiche l'état du WiFi et de la clé API sur l'écran d'information."""
    self.clear()  # Efface l'écran pour l'affichage des informations.

    # Affichage pour l'état du WiFi
    if wifi_status:
        draw_word_4(self.graphics, "WIFI ", 1, 2, self.pens['WHITE'])
        draw_word_4(self.graphics, "OK", 22, 2, self.pens['GREEN'])
    else:
        draw_word_4(self.graphics, "WIFI ", 1, 2, self.pens['WHITE'])
        draw_word_4(self.graphics, "KO", 22, 2, self.pens['RED'])

    # Affichage pour l'état de la clé API
    if api_key_status:
        draw_word_4(self.graphics, "API ", 1, 10, self.pens['WHITE'])
        draw_word_4(self.graphics, "OK", 22, 10, self.pens['GREEN'])
    else:
        draw_word_3(self.graphics, "API ", 1, 10, self.pens['WHITE'])
        draw_word_3(self.graphics, "KO", 22, 10, self.pens['RED'])

    self.update()  # Met à jour l'affichage avec les informations.

# Fonction d'affichage de l'écran d'accueil
def display_legend_screen(display):
    """Affiche l'écran légende avec les pixels identifiés"""
    display.clear()  # Efface l'écran pour l'affichage des informations.

    # Affichage légende pour le son OFF
    if 'RED' in display.pens:
        display.set_pen('RED')
        sound_off_red = [(1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (2, 4)]
        for x, y in sound_off_red:
            display.graphics.pixel(x, y)
    else:
        print("Erreur: Couleur 'RED' non définie dans display.pens")

    draw_word_3(display.graphics, "SON OFF", 5, 0, display.pens['WHITE'])

    # Affichage légende pour le WiFi (OFF)
    if 'RED' in display.pens:
        display.set_pen('RED')
        wifi_ko = [(0, 8), (1, 7), (1, 8), (1, 9), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10)]
        for x, y in wifi_ko:
            display.graphics.pixel(x, y)
    else:
        print("Erreur: Couleur 'RED' non définie dans display.pens")

    draw_word_3(display.graphics, "WIFI OFF", 5, 6, display.pens['WHITE'])

    # Affichage légende pour la boucle (loop)
    if 'YELLOW' in display.pens:
        display.set_pen('YELLOW')
        loop_led = [(1, 14)]
        for x, y in loop_led:
            display.graphics.pixel(x, y)
    else:
        print("Erreur: Couleur 'WHITE' non définie dans display.pens")

    draw_word_3(display.graphics, "NOM FIX", 3, 12, display.pens['WHITE'])

    # Met à jour l'affichage avec les informations.
    display.update()

# Attente de la pression du bouton pour démarrer le script principal
def wait_for_start(display, cu):
    """Affiche l'écran d'accueil et attend la pression du bouton C pour lancer le script principal."""
    display_welcome_screen(display)  # Affiche le message d'accueil
    print("Attente de la pression du bouton C pour démarrer...")

    # Boucle pour attendre la pression du bouton C
    while True:
        if cu.is_pressed(CosmicUnicorn.SWITCH_C):
            print("Bouton C pressé - Lancement du script principal.")
            time.sleep(0.5)  # Petite pause pour éviter les rebonds
            break  # Sortie de la boucle et début du script principal
        time.sleep(0.1)  # Vérifie le bouton à intervalles réguliers

# Fonction pour supprimer les accents : définit sur é et è
def normalize_name(text):
    """Remplace manuellement les accents par leurs équivalents non accentués et met le texte en majuscules."""
    accents = {
        'è': 'e', 'é': 'e',
    }
    # Remplacer chaque caractère accentué par son équivalent non accentué
    return ''.join(accents.get(c, c) for c in text).upper()

# Fonction pour arrêter proprement le script.
def stop_script(display, wifi_issue=False):
    """Arrête proprement le script et attend un redémarrage via le bouton D."""
    print("Arrêt du script demandé...")

    # Affiche "NO WIFI\nREBOOT\nPRESS D" centré si l'arrêt est causé par une perte de connexion WiFi
    message_lines = ["NO WIFI", "REBOOT", "PRESS D"] if wifi_issue else ["KO", "REBOOT", "PRESS D"]
    display.graphics.set_pen(display.pens['BLACK'])  # Définit le fond noir
    display.graphics.clear()  # Efface l'écran

    # Utilise draw_word_4 pour afficher le message d'arrêt sur l'écran
    display.set_pen('RED')
    y_offset = 2
    for line in message_lines:
        draw_word_4(display.graphics, line, 2, y_offset, display.pens['RED'])
        y_offset += 10  # Augmente l'offset vertical pour chaque ligne

    display.update()  # Met à jour l'affichage pour refléter le message final

    # Attente de l'appui sur le bouton D pour redémarrer
    while True:
        if display.cu.is_pressed(CosmicUnicorn.SWITCH_D):
            print("Redémarrage suite à la pression du bouton D.")
            time.sleep(1)  # Petite pause pour éviter plusieurs déclenchements
            machine.reset()  # Redémarrage

# Fonction pour charger les informations de connexion WiFi et clé API depuis le fichier "information.env"
def load_credentials(file_path):
    """Charge les informations de connexion WiFi (SSID, mot de passe) et la clé API depuis un fichier."""
    credentials = {}
    try:
        with open(file_path, "r") as f:  # Ouvre le fichier contenant les informations.
            for line in f:
                key, value = line.strip().split('=')  # Sépare les lignes par '=' pour extraire les informations.
                credentials[key.strip()] = value.strip()  # Stocke les informations dans un dictionnaire.
    except OSError:
        print(f"Erreur : impossible de trouver ou lire le fichier {file_path}")
    return credentials  # Retourne le dictionnaire contenant les informations.

# Fonction pour se connecter au WiFi
def connect_wifi(ssid, password, display, max_attempts=10):
    """Tente de se connecter au réseau WiFi avec un maximum de tentatives, avec animation."""
    wlan = network.WLAN(network.STA_IF)  # Initialise l'interface WiFi en mode station (client)
    wlan.active(True)  # Active l'interface WiFi
    attempts = 0  # Initialise le compteur de tentatives

    while not wlan.isconnected() and attempts < max_attempts:
        print(f"Connexion à {ssid}... Tentative {attempts + 1}/{max_attempts}")

        # Ajout de l'animation de chargement pendant la tentative de connexion
        loading_animation_step(display, attempts)

        wlan.connect(ssid, password)  # Lance la connexion au réseau WiFi avec les informations fournies
        time.sleep(3)  # Attend 3 secondes entre les tentatives
        attempts += 1

    if wlan.isconnected():
        print(f"WiFi connecté avec l'IP : {wlan.ifconfig()[0]}")
        return wlan  # Retourne l'objet wlan si la connexion est établie
    else:
        print("Échec de la connexion WiFi après plusieurs tentatives.")
        return None  # Retourne None si la connexion échoue

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
def handle_button_press(cu, display):
    """Gère les pressions des boutons A et D sur tous les écrans et ajuste le volume."""
    if cu.is_pressed(CosmicUnicorn.SWITCH_A):  # Si le bouton A est pressé
        display.toggle_sound()  # Active ou désactive le son
    if cu.is_pressed(CosmicUnicorn.SWITCH_D):  # Si le bouton D est pressé pour redémarrer
        print("Bouton D pressé - Redémarrage...")
        time.sleep(1)  # Attendre 1 seconde avant le redémarrage
        machine.reset()  # Redémarre la carte
    display.adjust_volume()  # Ajuste le volume avec les boutons de volume


def main_loop(display, start_time, synced, api_key, wlan):
    display.clear()  # Efface l'écran avant d'afficher le message d'attente
    display.display_message_frame_2("WAIT")
    time.sleep(2)

    tableau_agences = get_agency_data(api_key)
    if not tableau_agences:
        display.display_message_frame_2("NO API")
        time.sleep(5)
        return

    current_index = 0

    while True:
        try:
            # Vérification WiFi une seule fois au début de chaque agence
            wifi_status = display.check_wifi_status(wlan)
            display.update_led_wifi_status(wifi_status)

            agence_id, name, waiting_time = tableau_agences[current_index]

            # Mise à jour des données de l'agence
            if update_single_agency(api_key, tableau_agences[current_index]):
                print(f"Agence mise à jour : {name}, Temps d'attente mis à jour.")
            else:
                print(f"Affichage des anciennes données pour : {name}")

            # Détermine l'humeur en fonction du temps d'attente
            mood = 'happy' if waiting_time < 300000 else 'neutral' if waiting_time < 600000 else 'sad'
            display.clear()
            display.draw_frame(0, 6, 'YELLOW')
            display.draw_text_opt()
            display.draw_smiley(mood)
            display.set_transition_variable(name)

            print(f"Agence affichée : {name}, ID : {agence_id}, Temps d'attente : {waiting_time // 60000} minutes")

            # Affichage de l'agence et défilement du texte
            iteration_count = 0
            while iteration_count < 100:
                # Bouton C - Retour à l'écran d'accueil
                if display.cu.is_pressed(CosmicUnicorn.SWITCH_C):
                    print("Bouton C pressé - Retour à l'écran d'accueil.")
                    display.play_bip(500)  # Émettre un bip
                    time.sleep(0.5)  # Petite pause pour éviter les rebonds du bouton
                    return

                # Bouton B - Mettre en pause/reprendre la boucle
                if display.cu.is_pressed(CosmicUnicorn.SWITCH_B):
                    display.toggle_loop_pause()
                    time.sleep(0.5)  # Petite pause pour éviter les rebonds du bouton

                # Si la boucle est en pause, continue le défilement du texte et l'affichage de l'heure
                if display.loop_paused:
                    display.scroll_text(display.transition_var)
                    display.display_clock(start_time, synced)
                    display.adjust_brightness()
                    display.adjust_volume()
                    handle_button_press(display.cu, display)
                    time.sleep(0.1)
                    continue

                # Défilement normal si la boucle n'est pas en pause
                display.scroll_text(display.transition_var)
                display.display_clock(start_time, synced)
                display.adjust_brightness()
                display.adjust_volume()
                handle_button_press(display.cu, display)
                time.sleep(0.1)
                iteration_count += 1

            # Passe à l'agence suivante si la boucle n'est pas en pause
            if not display.loop_paused:
                current_index = (current_index + 1) % len(tableau_agences)

        except Exception as e:
            print(f"Erreur lors de la boucle d'affichage des agences : {e}")
            time.sleep(2)  # Attente avant de réessayer en cas d'erreur

        # Désactiver les LEDs du son en quittant l'affichage de l'agence
        display.update_led_sound_status(False)



# Fonction main pour afficher la page d'accueil avec le message "UNC OPT".
def main():
    """Fonction principale qui initialise l'affichage de l'accueil et attend le bouton C pour démarrer."""
    display = CosmicUnicornDisplay()  # Initialise l'affichage
    cu = display.cu  # Récupère l'instance pour gérer les boutons

    credentials = load_credentials("information.env")
    wlan = connect_wifi(credentials['SSID'], credentials['WIFI_PASSWORD'], display)

    if wlan:
        synced = sync_time()
        start_time = time.time()
        wifi_status = True  # Initialisation à True si la connexion est établie
    else:
        print("Impossible de démarrer le script sans connexion Wi-Fi.")
        stop_script(display, wifi_issue=True)  # Afficher "NO WIFI\n REBOOT" et attendre la pression du bouton D
        return

    api_key_status = credentials.get('API_KEY') is not None

    # Liste des fonctions d'affichage (accueil, info, légende, agences)
    display_modes = [
        display_welcome_screen,  # Appelle la fonction d'accueil avec l'animation du cœur
        display_info_screen,
        display_legend_screen,
        lambda d: main_loop(d, start_time, synced, credentials['API_KEY'], wlan)  # Main loop pour les agences
    ]

    current_mode = 0

    while True:
        # Mettez à jour `display_mode` pour indiquer quel écran est affiché
        display.display_mode = current_mode

        # Appel de la fonction d'affichage appropriée avec les bons arguments
        if current_mode == 1:  # Mode info, nécessite wifi_status et api_key_status
            display_modes[current_mode](display, wifi_status, api_key_status)
        else:
            display_modes[current_mode](display)

        while True:
            handle_button_press(cu, display)

            if cu.is_pressed(CosmicUnicorn.SWITCH_C):
                current_mode = (current_mode + 1) % len(display_modes)
                display.display_mode = current_mode  # Mettre à jour le mode d'affichage
                display.play_bip(500)  # Émettre un bip à chaque pression de C
                time.sleep(0.5)
                break

            time.sleep(0.1)


# Démarrer le programme avec la fonction main()
main()




