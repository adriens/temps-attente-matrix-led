# Cosmic Unicorn Project Setup

This guide explains how to set up the Cosmic Unicorn project, including configuring WiFi, copying necessary files, and deploying the display scenes. Follow these steps to get started.

# Prerequisites

**Hardware**: Pimoroni Cosmic-Unicorn 32x32 LED matrix with Raspberry Pi Pico W.

**Software**: Thonny IDE (required for file uploads and troubleshooting), GitHub access, WiFi credentials.

**Files Needed**:
  - `boot.py`: The boot file to ensure the script runs automatically.
  - `main.py`: The main Python script.
  - `information.env`: File containing WiFi credentials and the API key.

# 1. Install Thonny IDE

Download and install Thonny IDE from [thonny.org](https://thonny.org/). Thonny is **required** for this project, but only to manage file uploads and necessary modifications (such as customizing the `information.env` file). Thonny can also be used to troubleshoot issues.

## Using Thonny for the project:
- **File Upload**: Use Thonny to upload `boot.py`, `main.py`, and `information.env` to the Pimoroni Cosmic-Unicorn.
- **Modifying `information.env`**: Customize the WiFi credentials and API key in the `information.env` file.
- **Troubleshooting**: Thonny is used to diagnose issues and test scripts on the LED matrice.


# 2. Clone the GitHub Repository

Clone the repository to your local machine:
  git clone https://github.com/adriens/temps-attente-matrix-led.git

Navigate to the project directory
  cd temps-attente-matrix-led

# 3. Configure WiFi Credentials and API Key

**Edit the .env file** to provide your **WiFi credentials** :
SSID=<your-SSID>
WIFI_PASSWORD=<your-password>

Add your **API key** in the format :
  API_KEY=<your-api-key>

# 4. Copy Files to Raspberry Pi Pico

Connect your Raspberry Pi Pico W to your computer.

Open Thonny and select the correct interpreter for Raspberry Pi Pico W.
Save the following files to the Pico’s root directory:
- boot.py
- main.py
- information.env
Use Thonny’s file browser to ensure these files are saved correctly on the Pico.

# 6. Running the Script

Once the files are uploaded, the Pimoroni Cosmic-Unicorn will run autonomously as soon as it is powered on. No further intervention via Thonny is required for final usage.

# 7. Troubleshooting

* **WiFi Not Connecting**: Ensure correct SSID/password in the .env file and check network availability.
* **API Key Issues**: Make sure the API key in the .env file is correct and the file is in the correct directory.
* **Button Response Not Working**: Ensure the Cosmic Unicorn device buttons are functioning correctly and properly mapped.

# 8. Updating the Script

If there are any changes to the script, make sure to copy the updated version to the Raspberry Pi Pico.
Use Thonny IDE to overwrite the old script on the Pico's filesystem.

# 9. Volume and Brightness Adjustment

* **Volume**: Use the buttons on the Cosmic Unicorn to adjust the sound volume during runtime.
* **Brightness**: Adjust the brightness using the appropriate buttons on the Cosmic Unicorn.

# 10. Button Functionalities
* ***Button A "SOUND"**: Toggles the sound of the LED matrix on and off.
*-* **Button B "LOOP"**: During the agency display, if you wish to remain on the currently shown agency, pressing this button locks the display loop to prevent automatic changes.
*-* **Button C "DISPLAY"**: During the display phase, pressing this button cycles through the different screens (Home, Information, Legend, Agencies, QR_Code).
*-* **Button D "RESTART"**: Restarts the LED matrix.
*-* **Volume +/- Buttons**: Adjust the sound intensity of the LED matrix.
*-* **Brightness +/- Buttons**: Adjust the brightness of the LED matrix.

# Additional Notes
Feedback and Contributions: If you'd like to contribute or provide feedback on this guide, please open an issue or submit a pull request on GitHub.
