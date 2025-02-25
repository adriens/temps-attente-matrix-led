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
* **Button A "SOUND"**: Toggles the sound of the LED matrix on and off.
* **Button B "LOOP"**: During the agency display, if you wish to remain on the currently shown agency, pressing this button locks the display loop to prevent automatic changes.
* **Button C "DISPLAY"**: During the display phase, pressing this button cycles through the different screens (Home, Information, Legend, Agencies, QR_Code).
* **Button D "RESTART"**: Restarts the LED matrix.
* **Volume +/- Buttons**: Adjust the sound intensity of the LED matrix.
* **Brightness +/- Buttons**: Adjust the brightness of the LED matrix.

# 11. Troubleshooting

## 11.1 Debugging and Connecting with Thonny
If your Cosmic Unicorn starts automatically and launches the script, it may block access to the REPL and prevent Thonny from taking control. 
To properly connect Thonny and upload or modify your code, follow these steps:
1. **Manual Reset of the Board**
   - Press the reset button (or perform a hard reset) on your Raspberry Pi Pico W.
   - This will interrupt the running script.
2. **Connecting via Thonny**
   - Once the board has restarted, open Thonny and select the interpreter corresponding to your Raspberry Pi Pico W.
   - Thonny should then be able to connect to the REPL, allowing you to upload and manage your code.
This procedure ensures that the board is not blocked by the automatic script execution, and you can interact with it via Thonny for any debugging or updating operations.

## 11.2 Hard Reset and/or Upgrade Firmware
To perform a hard reset—preventing the script from automatically running and allowing you to upload your files via Thonny—follow these steps:
1. **Hard Reset in BOOTSEL Mode**
   - Disconnect the board.
   - Hold down the BOOTSEL button (located near the USB port) while reconnecting the Raspberry Pi Pico W to your computer.
   - Release the BOOTSEL button once the board is connected.
   - The board will then appear as a USB storage device. In this mode, the script will not run automatically, allowing you to access the REPL.
2. **Connecting via Thonny**
   - Open Thonny and select the MicroPython (Raspberry Pi Pico) interpreter.
   - Select the firmware for Pimoroni-CosmicUnicorn.
   - Execute the task to download and upload this firmware.
Once completed, you will be able to access the board via the REPL through Thonny.

## 11.3 Flashing the Matrix
To completely flash the firmware on your Cosmic Unicorn board, follow these steps:
1. **Enter BOOTSEL Mode:**  
   - Disconnect your Raspberry Pi Pico W from your computer.  
   - Hold down the **BOOTSEL** button (located near the USB port) while reconnecting the board to your computer.  
   - Release the **BOOTSEL** button once the board is connected.  
   - The board will appear as a USB mass storage device.
2. **Flash the Firmware:**  
   - Open Windows Explorer and navigate to the newly appeared USB drive.  
   - Copy the file **`cosmic_unicorn_flash_nuke.uf2`** to the drive. This file will completely reset the board and erase the current firmware.  
   - Once the reset is complete, copy the file **`cosmic_unicorn-v1.23.0-1-pimoroni-micropython.uf2`** to the same drive to flash the new firmware.
3. **Reconnect and Access via Thonny:**  
   - Safely eject the USB drive and disconnect the board.  
   - Reconnect the board normally (without holding BOOTSEL).  
   - Open Thonny and select the MicroPython (Raspberry Pi Pico) interpreter.  
   - You should now be able to access the board’s REPL and manage your files as needed.
This procedure ensures a complete firmware flash, allowing you to regain full control over the board via Thonny.

# Additional Notes
Feedback and Contributions: If you'd like to contribute or provide feedback on this guide, please open an issue or submit a pull request on GitHub.
