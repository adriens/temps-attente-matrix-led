# Cosmic Unicorn Project Setup

This guide explains how to set up the Cosmic Unicorn project, including configuring WiFi, copying necessary files, and deploying the display scenes. Follow these steps to get started:

# Prerequisites

**Hardware**: Pimoroni Cosmic-Unicorn 32x32 LED matrix with Raspberry Pi Pico W.

**Software**: Thonny IDE, GitHub access, WiFi credentials.

**Files Needed**:
  - cosmic_unicorn_script.py: The main Python script.
  - .env: File containing the API key for accessing agency data.

# 1. Install Thonny IDE (optional)

Download Thonny IDE from thonny.org.
Follow the installation instructions for your operating system.
The Thonny IDE may be necessary in case of **debugging the script or its behavior. It can also be used to implement/modify the .env file**.

# 2. Clone the GitHub Repository

Clone the repository to your local machine:
  git clone https://github.com/adriens/temps-attente-matrix-led.git

Navigate to the project directory
  cd temps-attente-matrix-led

# 3. Configure WiFi Credentials

**Edit the .env file** to provide your **WiFi credentials** :
  SSID=<your-SSID>
  PWD=<your-password>

# 5. Configure API Key

**Open the .env** file and add your API key in the format :
  API_KEY=<your-api-key>

# 4. Copy Files to Raspberry Pi Pico

Connect your Raspberry Pi Pico W to your computer.
In Thonny, ensure the **correct interpreter** (Raspberry Pi Pico) is selected.
Step 1: Verify that the COM port is active and connected to the Pico.
Step 2: Save the following files to the Pico's root directory:
  - `cosmic_unicorn_script.py`
  - `.env`
Step 3: Confirm that the script and API key file are correctly saved on the Pico by using the file browser in Thonny to view the files on the device.

# 6. Running the Script

Open cosmic_unicorn_script.py in Thonny.
Click the Run button to start executing the script.
The Cosmic Unicorn will display the initial setup status and then proceed to show agency waiting times and clock.

# 7. Troubleshooting

* **WiFi Not Connecting**: Ensure correct SSID/password, and check network availability.
* **API Key Issues**: Make sure the API key in api_key.env is correct and the file is in the correct directory.
* **Button Response Not Working**: Ensure the Cosmic Unicorn device buttons are functioning correctly and properly mapped.

# 8. Updating the Script

If there are any changes to the script, make sure to copy the updated version to the Raspberry Pi Pico.
Use Thonny IDE to overwrite the old script on the Pico's filesystem.

# 9. Volume and Brightness Adjustment

* **Volume**: Use the buttons on the Cosmic Unicorn to adjust the sound volume during runtime.
* **Brightness**: Adjust the brightness using the appropriate buttons on the Cosmic Unicorn.

# 10. Button A and B Functionality

* **Button A**: Toggles the sound on and off. When the sound is enabled, a beep will play to indicate activation.
* **Button B**: Pauses or resumes the main display loop. When paused, a yellow LED will indicate the pause status.

# Additional Notes

Feedback and Contributions: If you'd like to contribute or provide feedback on this guide, please open an issue or submit a pull request on GitHub.
