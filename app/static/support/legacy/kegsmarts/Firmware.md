# PicoBrew KegSmarts™ Firmware

*This page contains the latest version of the KegSmarts™ firmware and a running changelog of software updates made available by PicoBrew. For installation instructions and tools, please click [here](Firmware-Installation.md).*

**Latest Version: 1.0.6**
**Last Updated: August 14th, 2017**
[Click Here to Download Latest KegSmarts™ Firmware](KegSmarts_1_0_6.zip)
[Click Here to Download CC3000 WiFi Chip Firmware](../common/WiFiPatch.zip)

## Change Log

* **Version 1.0.6**
    * Fixed issue with connecting two keg warmers
    * Slowed down the read speed of keg plates
    * Added MAC address to about screen
* **Version 1.0.5**
    * Fixed issue introduced in KegPlates, reverted back
    * Fixed Screen menu bug
    * Fixed Kegerator temperature setting issue from website
    * Fixed Pico fermentations to load reliably
* **Version 1.0.4**
    * bug fixes for fermentation
    * added remove keg plate option
    * added error reporting if kegplate of heat jacket becomes unresponsive
    * fixed race condition with website setting kegerator temperature
    * bug fixes for kegplate readings
    * added test menu on power up, hold down encoder on power up of kegsmarts to access test menu
* **Version 1.0.3**
    * Fix for temperature regulation ignoring user input
    * CO2 fix for refilling
    * two heat jacket attachment fix
    * Known Issue: when switching steps from website fermentation immediately starts time counter for next step.
    * NOTE: When using test KegPlate function, kegplate values are only read if plate is assigned to a tap. If a KegPlate is not assigned to a tap system does not read weight readings from KegPlate (this does not apply to c02 plates).
* **Version 1.0.2**
    * updated communication protocol with server
    * fixed heat jacket remaining on when nothing is heating
    * changed temperature regulation hierarchy
    * added CO2 plate functionality
* **Version 1.0.1**
    * Fixed changing AP during startup
    * Fixed flashing to Zymatic potentially causing problems
* **Version 1.0.0**
    * initial release
