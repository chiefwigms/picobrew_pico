# PicoBrew Zymatic® Firmware

*This page contains the latest version of the Zymatic® firmware and a running changelog of software updates made available by PicoBrew. For installation instructions and tools, please click [here](Firmware-Installation.md).*

**Latest Version: 1.1.14**
**Last Updated: February 9th, 2017**
[Click Here to Download Latest Zymatic® Firmware](legacy/zymatic/Zymatic_1_1_14.zip)
[Click Here to Download CC3000 WiFi Chip Firmware](../common/WiFiPatch.zip)

## Change Log

* **Version 1.1.14**
    * Fixed bug in pause, Moved to Drain/Pause option
    * Added MAC addresses to About Zymatic (also added About Zymatic to test menu)
* **Version 1.1.13**
    * Added Pause feature to brewing, located in the context menu during brewing
    * Added delayed start feature, set the amount of time to wait before the brew begins, the machine will load the recipe you want to brew before you set the delay time
* **Version 1.1.12**
    * Fix for step name bug (step name not storing properly on machine)
* **Version 1.1.11**
    * Changed PID to ease up when maintaining also to reset values between steps
    * Changed where PID current temperature is being updated to the interrupt so if WiFi hangs we will not see spike in temperature due to non-updating PID outside of main loop (how it was originally done)
    * Correctly track drain time so when put in drain or if in error state (step filter removed) time in step will not be effected
    * Re-routed test menu so it no longer will connect to internet but rather (after stepper calibration) will boot directly into test menu (easing the life of customer service)
    * Fixed the new firmware setup to allow for new AP to solve the problem where if you connect to say a hotel network where you can connect to the AP and the internet but not actually do anything once connected
    * Added Firmware checking API so machine will tell user if there is new firmware available on site
    * Added ability to have 25 steps in a program. (to use this feature make sure to run a rinse cycle on the new firmware first so the website will allow you take advantage of this new feature)
    * Fixed drain issue from version 1.1.10
* **Version 1.1.9**
    * added @ symbol to keyboard
    * fixed WEP not being able to accept passwords with '00'
    * fine tuned heat logic (heating should take less time ~5 minutes)
    * added factory reset to make changing username simpler
    * added WiFi diagnostics to help menu
    * added more helpful error messaging and trouble shooting when first setting up Zymatic
    * fixed capital Q bug
    * made AP name storage up to 32 characters
    * reduced memory foot print on machine
    * fixed bug in error logging heater
    * NOTE: you will have to enter you WiFi info again on Zymatic when updating to this firmware after that it will store and re-logon like expected
* **Version 1.1.8**
    * When Delta T occurs a final data point is logged
    * added a WiFi re-scan feature so user doesn't have to turn off machine if WiFi is not found on initial scan
    * removed the false positive for chilling if wort were to read 32 or -1 this would occur
    * equalizing temps added to avoid delta T at start of brew
    * Jumpy Encoder on keyboard menu fixed
    * WiFi password can now be up to 32 characters (this is the limit the CC3000 can handle) which supports up to 128 bit encryption where before we only had up to 64
    * equalizing temps will not happen if the brew resets as it is already run whenever the machine restarts a brew after reset anyway
    * added dont care value for hitting temperature, if the temperature is set on the site as 0, then the machine essitially will run a timed circulate for the amount of time designated from the crafter.
* **Version 1.1.4**
    * WiFi updates
    * Recovery of brew fixes
    * more extensive error reporting to server
    * Added Re-Sync option to brew recipe menu
    * memory coherency checks added
    * minor bug fixes
* **Version 1.1.0**
    * WiFi Updates
    * Brew Display Modifications
    * Minor bug Fixes
* **Version 1.0.0**
    * Minor bug Fixes
