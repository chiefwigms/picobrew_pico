# PicoBrew Zymatic® Firmware Installation

*This page contains instructions and tools for updating your Zymatic® firmware.
For information on the latest firmware for your Zymatic®, please click [here](Firmware.md).*

## Quick Downloads

[PicoFlash Utility](../common/PicoFlash.zip)
[Latest Zymatic® Firmware](Zymatic_1_1_14.zip)

## Installation Instructions

1. **Download And Install the PicoFlash Utility**
    * Download the PicoFlash utility [here](../common/PicoFlash.zip).
    * A zipped folder will be downloaded to your downloads folder unless you specify another location or have a set preference for your browser.
    * Navigate to your downloads folder (or the folder that the downloaded PicoFlash file was stored).
    * Unzip the file by right clicking on the file and selecting "extract all".
    * When prompted to choose a destination for the unzipped files, we recommend creating a folder to keep the files together.
    * *Note: If you have an application installed to handle zipped folders you may need to take different steps then the ones listed above.*
    * Double-click the installer (PicoBrew Zymatic.exe) and proceed through the installation.
    * *Note: There are other files that are loaded for the installation process. If you are not sure which one is the .exe file, you can right click the files, select properties, and the type of file should be listed under the general tab of this properties window*
2. **Download Firmware**
    * Download the latest firmware [here](Zymatic_1_1_14.zip).
    * A zipped folder will be downloaded to your downloads folder unless you specify another location or have a set preference for your browser.
    * Navigate to your downloads folder (or the folder that the downloaded PicoFlash file was stored).
    * Unzip the file by right clicking on the file and selecting "extract all".
3. **Install the Firmware Using the PicoFlash Program**
    * IMPORTANT: Make sure your Zymatic® is powered ON and not brewing beer!
    * Connect your PC to the PicoBrew Zymatic® via USB.
    * Note: It may take a minute or two for your computer to recognize your Zymatic®. If an error message appers, wait one to two minutes before pressing "retry"
    * Open the PicoFlash utility, and click the ellipses button ![...](../common/ellipsesButton.png).
    * Navigate to the Zymatic® firmware you downloaded (.hex file) and select it.
    * Click ![FLASH Now!](../common/flashButton.png).
    * The utility will open a new window and show some progress bars while it installs the firmware on your Zymatic®.
    * When the utility has successfully completed updating the firmware, it will close automatically and restart your Zymatic®.
    * While the system is restarting, unplug the USB.
    * IMPORTANT: You must unplug the USB from your Zymatic® before you attempt to brew any beer or run any programs on the Zymatic®.
    * Once the machine has finished the new firmware setup, you will be prompted to select your username (just press the encoder) and your Zymatic® will display the normal welcome screen.
    * *Note: It is recommended that you power cycle the machine (turn the Zymatic® off and back on again) before brewing on any updated firmware.*
