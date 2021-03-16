#!/bin/bash

# hook to allow additional steps during an update. This gets called after
# a "git pull; pip3 install -r requirements.txt"
# and expects to have passwordless sudo

# figure out the absolute path to the root of the server install
script_dir=$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )
root_dir=${script_dir%/scripts/pi}
echo Using server root of $root_dir

allow_reboot=0
if [ "$1" == "--allow-reboot" ]; then
    allow_reboot=1
fi

# sanity check we are using the right root install
if [ ! -f $root_dir/config.yaml ]; then
    echo Unable to find $root_dir/config.yaml. Aborting...
    exit 1
fi

# older installs may not have had bluetooth support enabled/configured
# so add configuration and enable by default
if grep -q ^tilt_monitoring $root_dir/config.yaml; then
    echo Bluetooth already configured in config.yaml
else
    echo Adding bluetooth configuration \(enabled\) to config.yaml

    cat >> $root_dir/config.yaml <<EOF

# Enable Tilt support (bluetooth). Set to False to disable
tilt_monitoring: True
# the interval in seconds before checking for tilt data
tilt_monitoring_interval: 10
EOF
fi

# Raspberry Pi specific stuff here
if [ -f /proc/device-tree/model ] && grep -iq raspberry /proc/device-tree/model; then
    echo -n "Running on "; cat /proc/device-tree/model; echo

    # older raspberry-pi images had bluetooth disabled
    # so re-enable on those. This requires a reboot
    if grep -q "^dtoverlay\s*=\s*disable-bt" /boot/config.txt; then
        # allow a way for someone to intentionally disable bluetooth if so desired
        if grep -q picobrew_pico:intentionally-disable-bluetooth /boot/config.txt; then
            echo Bluetooth intentionally disabled. Leaving disabled...
        else
            echo Restoring OS bluetooth support in /boot/config.txt
            sudo sed -i "s/^dtoverlay\s*=\s*disable-bt/#&/" /boot/config.txt

            echo Making bluetooth accessible without being root...
            sudo setcap cap_net_raw+eip /usr/bin/python3.7
            sudo usermod -a -G bluetooth pi
            sudo systemctl restart dbus

            # best do this now to avoid any confusion
            if [ $allow_reboot -eq 1 ]; then
                echo Rebooting to enable changes. Will be right back...
                sudo shutdown -r now
            else
                echo A reboot will be required to enable bluetooth
            fi
        fi
    else
        echo Bluetooth already enabled at OS level
    fi
fi

exit 0