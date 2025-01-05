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
        self.graphics.set_font("bitmap5")  # Définit la police utilisée pour l'affichage du texte.
        self.sound_enabled = True  # Indique si le son est activé ou non.
        self.brightness = 0.5  # Définit la luminosité initiale de l'affichage.
        self.loop_paused = False  # Variable pour gérer la pause de la boucle d'affichage.
        self.volume = 500  # Fréquence initiale du bip sonore.
        self.pause_led_position = (1, 25)  # Position de la LED indiquant une pause.
        self.led_positions_sound_on = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # Positions des LEDs quand le son est activé.
        self.led_positions_sound_off = [(2, 9), (1, 10), (2, 10), (1, 11), (2, 11), (2, 12)]  # Positions des LEDs rouges quand le son est désactivé.
        self.led_positions_wifi_ko = [(0, 17), (1, 16), (1, 17), (1, 18), (2, 15), (2, 16), (2, 17), (2, 18), (2, 19)]
        self.channel = self.cu.synth_channel(5)  # Canal sonore pour gérer les bips sonores.
        self.cu.set_brightness(self.brightness)  # Définit la luminosité initiale de l'écran.
        self.display_mode = 0  # 0: Accueil, 1: Info, 2: Légende, 3: Agences, 4: QR Code
        self.update_led_sound_status()  # Met à jour les LEDs selon l'état du son.
        self.previous_wifi_status = False 
        print("Affichage initialisé avec succès")  # Confirmation de l'initialisation réussie.

    def clear(self):
        """Efface l'écran sans toucher aux LEDs du son et de pause."""
        self.graphics.set_pen(self.pens['BLACK'])  # Définit la couleur du stylo à noir pour effacer.
        self.graphics.clear()  # Efface l'écran.
        self.update_led_sound_status()  # Met à jour les LEDs du son.
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
        """Ajuste la luminosité en fonction des boutons de luminosité, avec confirmation de détection."""
        if self.cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_UP):  # Si le bouton pour augmenter la luminosité est pressé
            if self.brightness < 1.0:  # Limite supérieure pour la luminosité
                self.brightness = min(self.brightness + 0.1, 1.0)  # Augmente la luminosité par paliers
            print(f"Luminosité augmentée à : {self.brightness}")  # Message de débogage
        elif self.cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_DOWN):  # Si le bouton pour diminuer la luminosité est pressé
            if self.brightness > 0.0:  # Limite inférieure pour la luminosité
                self.brightness = max(self.brightness - 0.1, 0.0)  # Diminue la luminosité par paliers
            print(f"Luminosité diminuée à : {self.brightness}")  # Message de débogage
        self.cu.set_brightness(self.brightness)  # Applique la nouvelle luminosité

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
        self.display_digit(hour[0], 14, 1, 'YELLOW_SMILEY')  # Affiche le premier chiffre des heures.
        self.display_digit(hour[1], 18, 1, 'YELLOW_SMILEY')  # Affiche le deuxième chiffre des heures.
        if second % 2 == 0:  # Si les secondes sont paires, affiche les deux points de séparation.
            self.graphics.pixel(22, 2)
            self.graphics.pixel(22, 4)
        else:  # Sinon, les efface.
            self.set_pen('BLACK')
            self.graphics.pixel(22, 2)
            self.graphics.pixel(22, 4)
        self.display_digit(minute[0], 24, 1, 'YELLOW_SMILEY')  # Affiche le premier chiffre des minutes.
        self.display_digit(minute[1], 28, 1, 'YELLOW_SMILEY')  # Affiche le deuxième chiffre des minutes.
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
        self.sound_enabled = not self.sound_enabled  # Inverse l'état du son
        if self.sound_enabled:
            print("Son activé")
            self.play_bip(500)  # Émet un bip sonore
        else:
            print("Son désactivé")
            self.play_bip(400)  # Émet un bip différent
        self.update_led_sound_status()  # Met à jour l'état des LEDs

    # Fonction pour mettre à jour les LEDs en fonction de l'état du son (activé ou désactivé).
    def update_led_sound_status(self):
        """Met à jour les LEDs pour afficher l'état du son uniquement dans le mode agences."""
        if self.display_mode == 3:  # Afficher uniquement dans le mode agences
            if self.sound_enabled:
                self.set_pen('BLUE')
                for x, y in self.led_positions_sound_on:
                    self.graphics.pixel(x, y)
            else:
                self.set_pen('RED')
                for x, y in self.led_positions_sound_off:
                    self.graphics.pixel(x, y)
            self.update()
        else:
            self.clear_sound_leds()  # Efface les LEDs si ce n'est pas le bon mode
    
    def clear_sound_leds(self):
        """Efface les LEDs utilisées pour le statut du son."""
        self.set_pen('BLACK')
        for x, y in self.led_positions_sound_on:  # Même positions pour nettoyage
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
        """Vérifie l'état de la connexion WiFi et met à jour l'état des LEDs."""
        global attempts
        if wlan.isconnected():
            if not self.previous_wifi_status:
                print("WIFI OK")
                self.previous_wifi_status = True  # Mise à jour du statut
            attempts = 0  # Réinitialiser le compteur d'échecs
            return True
        else:
            if self.previous_wifi_status:
                print("WIFI KO")
                self.previous_wifi_status = False
            attempts += 1  # Incrémenter la variable d'échecs
            if attempts > 10:
                stop_script(self, wifi_issue=True)
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
def draw_word_4(graphics, word, x, y, display, color_name, spacing=5):
    """Dessine un mot entier en utilisant la lettre de taille 4 LED."""
    display.set_pen(color_name)  # Utilise set_pen pour appliquer la couleur
    current_x = x
    for letter in word:
        if letter in LETTER_MAP_4:
            for dx, dy in LETTER_MAP_4[letter]:
                graphics.pixel(current_x + dx, y + dy)
            current_x += spacing  # Espacement entre les lettres

def show_loading_screen(display, step):
    """Affiche l'animation de chargement et le texte WAIT avec la police bitmap5."""
    display.clear()
    display.graphics.set_font("bitmap5")  # Définit la police sur bitmap5
    display.graphics.set_pen(display.pens['WHITE'])  # Choisit le stylo blanc
    display.graphics.text("WAIT", 5, 12, scale=1)  # Affiche le texte "WAIT" en position (12, 14)
    loading_animation_step(display, step)  # Exécute l'étape de l'animation de chargement
    display.update()
    time.sleep(0.2)  # Pause pour la synchronisation de l'animation


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
        
def display_welcome_screen(display):
    """Affiche l'écran d'accueil avec 'UNC' défilant, puis dessine un bloc bleu autour de 'UNC' en inversant les couleurs."""
    display.display_mode = 0
    display.clear()  # Efface l'écran

    # Utilisation des couleurs pré-définies
    colors = {
        'UNC': 'BLUE',
        'OPT': 'YELLOW_SMILEY',
    }
    
    # Charger la police bitmap5
    display.graphics.set_font("bitmap5")

    # Positions de départ hors écran
    unc_x_start = display.width  # à droite, hors écran
    opt_x_start = -display.graphics.measure_text("OPT", 1)  # à gauche, hors écran

    # Positions finales
    unc_x_final = 2
    opt_x_final = 13

    # Boucle de défilement pour les deux textes
    while unc_x_start > unc_x_final or opt_x_start < opt_x_final:
        display.clear()

        # Afficher "UNC" en bleu, en défilant de droite à gauche
        if unc_x_start > unc_x_final:
            unc_x_start -= 1
        display.set_pen(colors['UNC'])
        display.graphics.text("UNC", unc_x_start, 1, scale=1)

        # Afficher "OPT" en jaune smiley, en défilant de gauche à droite
        if opt_x_start < opt_x_final:
            opt_x_start += 1
        display.set_pen(colors['OPT'])
        display.graphics.text("OPT", opt_x_start, 24, scale=1)

        # Mettre à jour l'affichage
        display.update()
        time.sleep(0.1)  # Ajustez pour la vitesse du défilement

    # Texte "UNC" en position finale avec inversion des couleurs
    display.set_pen(colors['UNC'])
    display.graphics.text("UNC", unc_x_final, 1, scale=1)
    display.update()
    time.sleep(0.5)
    # Couleur du fond en bleu et les lettres en noir
    display.set_pen('BLUE')
    for x in range(1, 19):
        for y in range(1, 8):
            display.graphics.pixel(x, y)
    # Laisser les LEDs de "UNC" en noir en repassant par-dessus
    display.set_pen('BLACK')
    unc_pixels = {
        # 'U'
        (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (6, 2), (6, 3), (6, 4), (6, 5),
        # 'N'
        (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (9, 2), (10, 2), (11, 2), (12, 2), (12, 3), (12, 4), (12, 5), (12, 6),
        # 'C'
        (14, 2), (14, 3), (14, 4), (14, 5), (14, 6), (15, 2), (16, 2), (17, 2), (15, 6), (16, 6), (17, 6),
    }
    for (x, y) in unc_pixels:
        display.graphics.pixel(x, y)

    # Texte "OPT" en position finale avec inversion des couleurs
    display.set_pen(colors['OPT'])
    display.graphics.text("OPT", opt_x_final, 24, scale=1)
    display.update()
    time.sleep(0.5)
    # Couleur du fond en jaune et les lettres en noir
    display.set_pen('YELLOW_SMILEY')
    for x in range(12, 31):
        for y in range(24, 31):
            display.graphics.pixel(x, y)  
    # Laisser les LEDs de "OPT" en noir en repassant par-dessus
    display.set_pen('BLACK')
    opt_pixels = {
        # 'O'
        (13, 25), (13, 26), (13, 27), (13, 28), (13, 29), (14, 25), (15, 25), (16, 25), (14, 29), (15, 29), (16, 29), (17, 29), (17, 26), (17, 27), (17, 28), (17, 29), 
        # 'P'
        (19, 25), (19, 26), (19, 27), (19, 28), (19, 29), (20, 25), (21, 25), (22, 25), (21, 28), (22, 28), (23, 28), (23, 25), (23, 26), (23, 27),
        # 'T'
        (25, 25), (26, 25), (27, 25), (28, 25), (29, 25), (27, 25), (27, 26), (27, 27), (27, 28),
    }
    for (x, y) in opt_pixels:
        display.graphics.pixel(x, y)

    # Mettre à jour pour afficher les blocs finaux
    display.update()
    time.sleep(0.5)

    # enchaîner avec l'animation
    exploding_heart_animation(display)


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


def display_info_screen(self, wifi_status, api_key_status, file_agences_status):
    """Affiche l'état du WiFi, de la clé API, et du fichier agences.env sur l'écran d'information."""
    self.display_mode = 1
    self.clear()  # Efface l'écran pour l'affichage des informations.

    # Définir la police et la couleur
    self.graphics.set_font("bitmap5")
    self.graphics.set_pen(self.pens['WHITE'])

    # Affichage pour l'état du WiFi
    self.graphics.text("WIFI", 1, 0, scale=1)
    if wifi_status:
        self.graphics.set_pen(self.pens['GREEN'])
        self.graphics.text("OK", 21, 0, scale=1)
    else:
        self.graphics.set_pen(self.pens['RED'])
        self.graphics.text("KO", 21, 0, scale=1)

    # Affichage pour l'état de la clé API
    self.graphics.set_pen(self.pens['WHITE'])
    self.graphics.text("API", 1, 8, scale=1)
    if api_key_status:
        self.graphics.set_pen(self.pens['GREEN'])
        self.graphics.text("OK", 21, 8, scale=1)
    else:
        self.graphics.set_pen(self.pens['RED'])
        self.graphics.text("KO", 21, 8, scale=1)

    # Affichage pour l'état du fichier agences.env
    self.graphics.set_pen(self.pens['WHITE'])
    self.graphics.text(".ENV", 1, 16, scale=1)
    if file_agences_status:
        self.graphics.set_pen(self.pens['GREEN'])
        self.graphics.text("OK", 21, 16, scale=1)
    else:
        self.graphics.set_pen(self.pens['RED'])
        self.graphics.text("KO", 21, 16, scale=1)
        
    # Affichage url bitly
    #self.graphics.set_pen(self.pens['WHITE'])
    #self.graphics.text("https://bit.ly/3AJbpj2", 1, 23, scale=1)

    self.update()  # Met à jour l'affichage avec les informations.


# Fonction d'affichage de l'écran des légendes
def display_legend_screen(display):
    """
    Affiche les messages en lettres spécifiques avec leur couleur et les LED icônes.
    Les messages sont ajustés pour être alignés avec leurs icônes LED.
    """
    display.clear()
    legends = [
        {"message": "SON ON", "color": "BLUE", "leds": [(0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (1, 5)], "x_offset": -2, "y_offset": -2},
        {"message": "SON OFF", "color": "RED", "leds": [(0, 9), (0, 10), (1, 8), (1, 9), (1, 10), (1, 11)], "x_offset": -2, "y_offset": -2},
        {"message": "NO WIFI", "color": "RED", "leds": [(0, 15), (1, 14), (1, 15), (1, 16), (2, 13), (2, 14), (2, 15), (2, 16), (2, 17)], "x_offset": -1, "y_offset": -2},
        {"message": "NO LOOP", "color": "YELLOW", "leds": [(1, 21)], "x_offset": -2, "y_offset": -2},
    ]

    for legend in legends:
        # Dessiner les LED icônes
        display.set_pen(legend["color"])
        for x, y in legend["leds"]:
            display.graphics.pixel(x, y)

        # Dessiner le message en map 4 avec ajustement de position
        draw_word_4(
            display.graphics,
            legend["message"],
            5 + legend["x_offset"],  # Décalage horizontal
            legend["leds"][0][1] + legend["y_offset"],  # Décalage vertical
            display,
            legend["color"]
        )

    display.update()

      
# QR CODE de l'adresse Bit.ly "https://bit.ly/3AJbpj2" (https://github.com/adriens/temps-attente-matrix-led)
led_white_positions = [
    (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (12, 4), (13, 4), (14, 4), (15, 4),
    (18, 4), (19, 4), (22, 4), (23, 4), (24, 4), (25, 4), (26, 4), (27, 4), (28, 4), (4, 5),
    (10, 5), (15, 5), (16, 5), (18, 5), (20, 5), (22, 5), (28, 5), (4, 6), (6, 6), (7, 6), (8, 6),
    (10, 6), (13, 6), (15, 6), (17, 6), (19, 6), (20, 6), (22, 6), (24, 6), (25, 6), (26, 6),
    (28, 6), (4, 7), (6, 7), (7, 7), (8, 7), (10, 7), (14, 7), (15, 7), (17, 7), (20, 7), (22, 7),
    (24, 7), (25, 7), (26, 7), (28, 7), (4, 8), (6, 8), (7, 8), (8, 8), (10, 8), (14, 8), (15, 8),
    (16, 8), (18, 8), (19, 8), (20, 8), (22, 8), (24, 8), (25, 8), (26, 8), (28, 8), (4, 9), (10, 9),
    (13, 9), (15, 9), (17, 9), (22, 9), (28, 9), (4, 10), (5, 10), (6, 10), (7, 10), (8, 10), (9, 10),
    (10, 10), (12, 10), (14, 10), (16, 10), (18, 10), (20, 10), (22, 10), (23, 10), (24, 10), (25, 10),
    (26, 10), (27, 10), (28, 10), (12, 11), (13, 11), (16, 11), (17, 11), (18, 11), (19, 11), (4, 12),
    (5, 12), (7, 12), (8, 12), (10, 12), (13, 12), (16, 12), (18, 12), (19, 12), (22, 12), (28, 12),
    (4, 13), (6, 13), (7, 13), (14, 13), (19, 13), (20, 13), (23, 13), (24, 13), (25, 13), (26, 13),
    (27, 13), (6, 14), (7, 14), (8, 14), (9, 14), (10, 14), (13, 14), (16, 14), (18, 14), (19, 14),
    (20, 14), (21, 14), (25, 14), (28, 14), (6, 15), (9, 15), (12, 15), (19, 15), (22, 15), (25, 15),
    (26, 15), (27, 15), (28, 15), (5, 16), (6, 16), (7, 16), (8, 16), (9, 16), (10, 16), (11, 16),
    (13, 16), (14, 16), (20, 16), (22, 16), (23, 16), (28, 16), (4, 17), (6, 17), (11, 17), (12, 17),
    (14, 17), (16, 17), (18, 17), (19, 17), (21, 17), (24, 17), (27, 17), (4, 18), (5, 18), (6, 18),
    (7, 18), (8, 18), (9, 18), (10, 18), (12, 18), (13, 18), (19, 18), (21, 18), (22, 18), (24, 18),
    (25, 18), (26, 18), (27, 18), (28, 18), (4, 19), (6, 19), (12, 19), (13, 19), (14, 19), (16, 19),
    (18, 19), (20, 19), (22, 19), (23, 19), (25, 19), (26, 19), (28, 19), (4, 20), (6, 20), (8, 20),
    (9, 20), (10, 20), (11, 20), (15, 20), (16, 20), (17, 20), (18, 20), (20, 20), (21, 20), (22, 20),
    (23, 20), (24, 20), (26, 20), (27, 20), (12, 21), (14, 21), (15, 21), (18, 21), (19, 21), (20, 21),
    (24, 21), (26, 21), (27, 21), (4, 22), (5, 22), (6, 22), (7, 22), (8, 22), (9, 22), (10, 22),
    (13, 22), (16, 22), (18, 22), (20, 22), (22, 22), (24, 22), (28, 22), (4, 23), (10, 23), (15, 23),
    (17, 23), (18, 23), (19, 23), (20, 23), (24, 23), (4, 24), (6, 24), (7, 24), (8, 24), (10, 24),
    (12, 24), (14, 24), (15, 24), (17, 24), (19, 24), (20, 24), (21, 24), (22, 24), (23, 24), (24, 24),
    (27, 24), (28, 24), (4, 25), (6, 25), (7, 25), (8, 25), (10, 25), (12, 25), (14, 25), (16, 25),
    (17, 25), (18, 25), (20, 25), (22, 25), (27, 25), (28, 25), (4, 26), (6, 26), (7, 26), (8, 26),
    (10, 26), (14, 26), (15, 26), (17, 26), (20, 26), (21, 26), (24, 26), (25, 26), (26, 26), (27, 26),
    (28, 26), (4, 27), (10, 27), (12, 27), (13, 27), (15, 27), (16, 27), (17, 27), (23, 27), (24, 27),
    (26, 27), (27, 27), (28, 27), (4, 28), (5, 28), (6, 28), (7, 28), (8, 28), (9, 28), (10, 28),
    (12, 28), (13, 28), (14, 28), (15, 28), (16, 28), (17, 28), (20, 28), (21, 28), (25, 28), (28, 28)
    ]


# Fonction d'affichage du QR code avec intégration de la luminosité définie dans la classe
def display_qr_code_screen(self):
    self.display_mode = 4
    self.clear()  # Efface l'écran pour un nouvel affichage

    # Affichage du QR code en tenant compte de la luminosité actuelle
    led_on_intensity = int(255 * self.brightness)
    self.graphics.set_pen(self.graphics.create_pen(0, 0, 0))
    self.graphics.clear()

    for x, y in led_white_positions:
        self.graphics.set_pen(self.graphics.create_pen(led_on_intensity, led_on_intensity, led_on_intensity))
        self.graphics.pixel(x, y)

    # Mettre à jour l'affichage pour refléter les changements
    self.update()

    # Boucle pour ajuster la luminosité en temps réel
    while True:
        self.adjust_brightness()  # Ajuste la luminosité en fonction des boutons de luminosité
        led_on_intensity = int(255 * self.brightness)
        for x, y in led_white_positions:
            self.graphics.set_pen(self.graphics.create_pen(led_on_intensity, led_on_intensity, led_on_intensity))
            self.graphics.pixel(x, y)
        self.update()
        
        # Interruption de la boucle avec le bouton C
        if self.cu.is_pressed(CosmicUnicorn.SWITCH_C):
            print("Bouton C pressé - Quitter l'écran QR code.")
            self.play_bip(500)  # Émettre un bip de confirmation
            break  # Sortie de la boucle pour passer à l'écran suivant

        time.sleep(0.1)


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
def stop_script(display, wifi_issue=False, api_issue=False):
    """Arrête proprement le script et attend un redémarrage via le bouton D."""
    print("Arrêt du script demandé...")

    # Sélection du message en fonction de la cause
    if wifi_issue:
        message_lines = ["NO WIFI", "REBOOT", "PRESS D"]
    elif api_issue:
        message_lines = ["KO API", "REBOOT", "PRESS D"]
    else:
        message_lines = ["KO", "REBOOT", "PRESS D"]

    display.clear()
    display.set_pen('RED')
    y_offset = 2
    for line in message_lines:
        draw_word_4(display.graphics, line, 2, y_offset, display.pens['RED'])
        y_offset += 10

    display.update()

    while True:
        if display.cu.is_pressed(CosmicUnicorn.SWITCH_D):
            print("Redémarrage suite à la pression du bouton D.")
            time.sleep(1)
            machine.reset()
        time.sleep(0.1)

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


# Fonction pour charger les agences depuis l'API
def load_agencies_from_api(api_key):
    """
    Charge les agences avec ID et Nom depuis le premier endpoint.
    Retourne un tableau structuré [ID, Nom, Temps d'attente initialisé à 0].
    """
    url = "https://api.opt.nc/temps-attente-agences/agences/iot"
    headers = {"x-apikey": api_key, "Accept": "application/json"}
    agencies = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        gc.collect()  # Libérer la mémoire après la requête

        if response.status_code == 200:
            data = response.json()
            for agency in data:
                agency_id = agency.get("idAgence")
                agency_name = agency.get("designation")
                if agency_id and agency_name:
                    agencies.append([agency_id, agency_name, 0])  # Temps initialisé à 0
            print("Agences chargées :", agencies)
            return agencies
        else:
            print(f"Erreur API : {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erreur lors de la récupération des agences : {e}")
    return []

# Fonction pour Initialise les temps d'attente pour les deux premières agences dans la liste
def initialize_agency_wait_times(api_key, agencies):
    """Initialise les temps d'attente pour toutes les agences."""
    for agency in agencies:
        if not update_single_agency(api_key, agency):
            print(f"Erreur : Échec de l'initialisation pour l'agence {agency[1]}")

# Fonction pour mettre à jour une seule agence avant l'affichage
def update_single_agency(api_key, agency):
    """Met à jour les données d'une agence spécifique en appelant l'API."""
    agence_id, name, old_waiting_time = agency
    url = f"https://api.opt.nc/temps-attente-agences/agences/{agence_id}"  # URL correcte
    headers = {"x-apikey": api_key, "Accept": "application/json"}
    
    # Vérification de la clé API
    if not api_key:
        print("Erreur : Clé API manquante.")
        return False
    
    # Vérification de l'ID de l'agence
    if not isinstance(agence_id, int):
        print(f"Erreur : ID d'agence invalide ({agence_id}).")
        return False

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            new_waiting_time = data.get('realMaxWaitingTimeMs', 0)
            agency[2] = new_waiting_time
            print(f"Temps mis à jour pour {name} : {new_waiting_time // 60000} minutes")
            return True
        else:
            print(f"Erreur API {response.status_code} pour {name} (ID: {agence_id})")
            print(f"Message de l'API : {response.text}")
    except Exception as e:
        print(f"Erreur réseau pour {name} (ID: {agence_id}) : {e}")
    return False

def initialize_agencies(api_key, agencies):
    """
    Met à jour le temps d'attente pour les agences dans le tableau.
    """
    for agency in agencies:
        success = update_agency_waiting_time(api_key, agency)
        if not success:
            print(f"Impossible de mettre à jour {agency[1]}")
        gc.collect()

def update_agency_waiting_time(api_key, agency):
    """
    Met à jour le temps d'attente pour une agence spécifique.
    agency : [ID, Nom, Temps] -> Met à jour Temps avec 'realMaxWaitingTimeMs'.
    """
    agency_id = agency[0]  # Récupère l'ID de l'agence
    url = f"https://api.opt.nc/temps-attente-agences/agences/{agency_id}"
    headers = {"x-apikey": api_key, "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        gc.collect()  # Libérer la mémoire après la requête

        if response.status_code == 200:
            data = response.json()
            waiting_time = data.get("realMaxWaitingTimeMs", 0)
            agency[2] = waiting_time  # Mise à jour du temps dans le tableau
            print(f"Temps mis à jour pour {agency[1]} : {waiting_time // 60000} minutes")
            return True
        else:
            print(f"Erreur API {response.status_code} pour {agency[1]}")
    except Exception as e:
        print(f"Erreur lors de la mise à jour pour {agency[1]} : {e}")
    return False



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


# Fonction qui gère la boucle dans la fonction principale main() pour l'affichage des agences
def main_loop(display, start_time, synced, api_key, wlan, tableau_agences):
    display.display_mode = 3  # Définir le mode agences
    display.clear()
    display.display_message_frame_2("WAIT")
    print("Démarrage de la boucle principale - affichage initial WAIT")
    time.sleep(2)

    current_index = 0
    next_index = (current_index + 1) % len(tableau_agences)

    # Mise à jour initiale uniquement pour la première agence
    if not update_single_agency(api_key, tableau_agences[current_index]):
        print(f"Erreur initiale de mise à jour pour {tableau_agences[current_index][1]}")

    while True:
        try:
            wifi_status = display.check_wifi_status(wlan)
            display.update_led_wifi_status(wifi_status)

            # Récupération des informations de l'agence
            agence_id, name, waiting_time = tableau_agences[current_index]
            mood = 'happy' if waiting_time < 300000 else 'neutral' if waiting_time < 600000 else 'sad'

            # Affichage des informations
            display.clear()
            #display.draw_frame(0, 6, 'YELLOW')
            display.draw_text_opt()  # Sigle OPT
            display.draw_smiley(mood)
            display.set_transition_variable(name)
            display.update_led_sound_status()
            print(f"Agence : {name}, Temps d'attente : {waiting_time // 60000} min")

            # Gestion des boutons A, B, C, D
            for _ in range(100):
                if display.cu.is_pressed(display.cu.SWITCH_A):
                    display.toggle_sound()

                if display.cu.is_pressed(display.cu.SWITCH_B):
                    display.toggle_loop_pause()

                if display.cu.is_pressed(display.cu.SWITCH_C):
                    print("Bouton C pressé - Changement d'écran.")
                    return

                if display.cu.is_pressed(display.cu.SWITCH_D):
                    print("Bouton D pressé - Reboot de la matrice.")
                    time.sleep(0.5)
                    machine.reset()

                if not display.loop_paused:
                    display.scroll_text(display.transition_var)
                    display.display_clock(start_time, synced)

                display.adjust_brightness()
                display.adjust_volume()
                time.sleep(0.1)

            # Mise à jour de l'agence suivante
            if not update_single_agency(api_key, tableau_agences[next_index]):
                print(f"Échec de mise à jour pour {tableau_agences[next_index][1]}")

            current_index = next_index
            next_index = (current_index + 1) % len(tableau_agences)

        except Exception as e:
            print(f"Erreur dans la boucle : {e}")
            time.sleep(2)


# Fonction main pour accéder aux différents affichages
def main():
    """Fonction principale avec initialisation, gestion des écrans et affichage des agences."""
    display = CosmicUnicornDisplay()
    cu = display.cu  # Gestion des boutons

    # Étape 1 : Affichage "WAIT" initial
    show_loading_screen(display, 0)
    print("Affichage initial 'WAIT'")

    # Charger les informations WiFi et API
    credentials = load_credentials("information.env")
    if not credentials:
        print("Erreur : Informations de connexion non trouvées.")
        stop_script(display)
        return

    api_key = credentials.get('API_KEY')
    if not api_key:
        print("Erreur : Clé API manquante.")
        stop_script(display)
        return

    wlan = connect_wifi(credentials['SSID'], credentials['WIFI_PASSWORD'], display)
    if not wlan:
        stop_script(display, wifi_issue=True)
        return

    show_loading_screen(display, 1)

    # Synchronisation NTP
    if not sync_time():
        print("Échec de la synchronisation NTP.")
    else:
        print("Synchronisation NTP réussie.")
    display.update_led_wifi_status(wlan.isconnected())

    # Charger les agences via le premier endpoint
    tableau_agences = load_agencies_from_api(api_key)
    if not tableau_agences:
        print("Erreur : Impossible de charger les agences.")
        stop_script(display, api_issue=True)
        return
    print(f"{len(tableau_agences)} agences chargées avec succès.")

    # Mise à jour uniquement de la première agence
    if not update_single_agency(api_key, tableau_agences[0]):
        print(f"Erreur : Échec de mise à jour initiale pour {tableau_agences[0][1]}.")

    show_loading_screen(display, 2)

    # Synchronisation de l'heure
    synced = sync_time() if wlan else False
    start_time = time.time()

    # Initialisation des LEDs pour le son
    display.update_led_sound_status()

    # Configuration des modes d'affichage
    display_modes = [
        display_welcome_screen,  # Écran d'accueil UNC/OPT
        lambda d: display_info_screen(d, wlan.isconnected(), True, True),  # Statut API/WiFi/ENV
        lambda d: display_legend_screen(d),  # Légendes des LEDs
        lambda d: main_loop(d, start_time, synced, api_key, wlan, tableau_agences),  # Affichage des agences
        lambda d: display_qr_code_screen(d)  # Écran QR Code Bit.ly
    ]

    current_mode = 0
    display_modes[current_mode](display)

    # Boucle principale pour gérer les changements d'écran avec le bouton C
    while True:
        handle_button_press(cu, display)

        # Bouton A : Activation/désactivation du son
        if cu.is_pressed(cu.SWITCH_A):
            display.toggle_sound()  # Change l'état du son et met à jour les LEDs
            time.sleep(0.5)

        # Bouton C : Basculer vers l'écran suivant
        if cu.is_pressed(CosmicUnicorn.SWITCH_C):
            current_mode = (current_mode + 1) % len(display_modes)
            display.play_bip(500)
            print("Passage à l'écran suivant.")
            time.sleep(0.5)
            display_modes[current_mode](display)

        time.sleep(0.1)


# Démarrer le programme avec la fonction main()
main()






