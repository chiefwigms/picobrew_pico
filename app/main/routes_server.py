import os
import re
import shlex
import subprocess
import sys
import traceback
from flask import current_app, make_response, request, redirect, send_file
from threading import Thread
from time import sleep

from . import main
from .config import base_path
from .frontend_common import platform, render_template_with_defaults, system_info


# -------- Routes --------
@main.route('/restart_server')
def restart_server():
    # git pull & install any updated requirements
    os.system('cd {0}; git pull; pip3 install -r requirements.txt'.format(base_path()))
    # TODO: Close file handles for open sessions?

    if platform() == "RaspberryPi":
        update_script = "./scripts/pi/post-git-update.sh"
        os.system('cd {0}; if [ -f {1} ]; then {1} --allow-reboot; fi'.format(base_path(), update_script))

    def restart():
        sleep(2)
        os.execl(sys.executable, *([sys.executable] + sys.argv))
    thread = Thread(target=restart, daemon=True)
    thread.start()
    return redirect('/')


@main.route('/restart_system')
def restart_system():
    if platform() != "RaspberryPi":
        return '', 404

    os.system('shutdown -r now')
    # TODO: redirect to a page with alert of restart
    return redirect('/')


@main.route('/shutdown_system')
def shutdown_system():
    if platform() != "RaspberryPi":
        return '', 404

    os.system('shutdown -h now')
    # TODO: redirect to a page with alert of shutdown
    return redirect('/')


@main.route('/logs')
def view_logs():
    if platform() != "RaspberryPi":
        return '', 404

    return render_template_with_defaults('logs.html')


@main.route('/logs/<log_type>.log')
def download_logs(log_type):
    if platform() != "RaspberryPi":
        return '', 404

    try:
        filename = ""
        if log_type == 'nginx.access':
            filename = "/var/log/nginx/picobrew.access.log"
        elif log_type == 'nginx.error':
            filename = "/var/log/nginx/picobrew.error.log"
        elif log_type == 'picobrew_pico':
            max_lines = request.args.get('max', 20000)
            filename = f"{current_app.config['BASE_PATH']}/app/logs/picobrew_pico.log"
            subprocess.check_output(f"systemctl status rc.local -n {max_lines} > {filename}", shell=True)
        else:
            error_msg = f"invalid log type specified {log_type} is unsupported"
            return error_msg, 400

        response = make_response(send_file(filename))
        # custom content-type will force a download vs rendering with window.location
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response
    except Exception as e:
        error = f'Unexpected Error Retrieving {log_type} log file:<br/> {e}'
        return error, 500


def available_networks():
    # TODO: properly handle failures by hiding settings in /setup or showing error

    wifi_list = subprocess.check_output('./scripts/pi/wifi_scan.sh | grep 2.4', shell=True)
    networks = []
    for network in wifi_list.split(b'\n'):
        network_parts = shlex.split(network.decode())
        if len(network_parts) == 6:
            networks.append({
                "bssid": network_parts[0],
                "ssid": network_parts[1],
                "frequency": network_parts[2],
                "channel": network_parts[3],
                "signal": network_parts[4],
                "encryption": network_parts[5]
            })
    return networks


@main.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        if platform() != "RaspberryPi":
            return '', 404

        payload = request.get_json()

        if 'hostname' in payload:
            # change the device hostname and reboot
            old_hostname = hostname()
            new_hostname = payload['hostname']

            # check if hostname is only a-z0-9\-\_
            if not re.match("^[a-zA-Z0-9\-_]+$", new_hostname):
                current_app.logger.error("ERROR: invalid hostname provided: {}".format(new_hostname))
                return 'Invalid Hostname (only supports a-z, 0-9, - and _ as characters)!', 400

            # allow systemd to update hostname
            subprocess.check_output(f"hostnamectl set-hostname --static {new_hostname}", shell=True)

            # restart for new host settings to take effect
            os.system('shutdown -r now')

            return '', 204
        elif 'interface' in payload:
            if payload['interface'] == 'wlan0':
                # change wireless configuration (wpa_supplicant-wlan0.conf and wpa_supplicant.conf)
                # sudo sed -i -e"s/^\bssid=.*/ssid=\"$SSID\"/" /etc/wpa_supplicant/wpa_supplicant.conf
                # sudo sed -i -e"s/^psk=.*/psk=\"$WIFIPASS\"/" /etc/wpa_supplicant/wpa_supplicant.conf

                try:
                    # <= beta4 => /etc/wpa_supplicant/wpa_supplicant.conf
                    # >= beta5 => /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
                    wpa_files = " ".join([_x for _x in ("/etc/wpa_supplicant/wpa_supplicant.conf", "/etc/wpa_supplicant/wpa_supplicant-wlan0.conf") if os.path.exists(_x)])

                    # set ssid in wpa_supplicant files
                    # regex \b marks a word boundary
                    ssid = payload['ssid']
                    subprocess.check_output(
                        """sed -i 's/\\bssid=.*/ssid="{}"/' {}""".format(ssid, wpa_files), shell=True)

                    # set bssid (if set by user) in wpa_supplicant files
                    if 'bssid' in payload and payload['bssid']:
                        bssid = payload['bssid']
                        # remove comment for bssid line (if present)
                        subprocess.check_output(
                            """sudo sed -i '/bssid/s/# *//g' {}""".format(wpa_files), shell=True)
                        subprocess.check_output(
                            """sudo sed -i 's/bssid=.*/bssid={}/' {}""".format(bssid, wpa_files), shell=True)
                    else:
                        # add a comment for bssid line (if present)
                        subprocess.check_output(
                            """sudo sed -i 's/\(bssid=.*\)/# \\1/g' {}""".format(wpa_files), shell=True)

                    # set credentials (if set by user) in wpa_supplicant files
                    if 'password' in payload:
                        psk = payload['password']
                        subprocess.check_output(
                            """sed -i 's/psk=.*/psk="{}"/' {}""".format(psk, wpa_files), shell=True)

                    def restart_wireless():
                        import subprocess
                        import time
                        time.sleep(2)
                        subprocess.check_output('systemctl restart wpa_supplicant@wlan0.service', shell=True)

                    # async restart wireless service
                    thread = Thread(target=restart_wireless)
                    current_app.logger.info("applying changes and restarting wireless interface")
                    thread.start()

                    return '', 204
                    # TODO: redirect to a page with alert of success or failure of wireless service reset
                except Exception:
                    current_app.logger.error("ERROR: error occured in wireless setup:", sys.exc_info()[2])
                    current_app.logger.error(traceback.format_exc())
                    return 'Wireless Setup Failed!', 418
            elif payload['interface'] == 'ap0':
                try:
                    hostapd_file = "/etc/hostapd/hostapd.conf"

                    # set ssid in hostapd file
                    ssid = payload['ssid']
                    subprocess.check_output(
                        """sed -i -e 's/ssid=.*/ssid={}/' {}""".format(ssid, hostapd_file), shell=True)

                    # set credentials (if set by user) in hostapd file
                    if 'password' in payload and payload['password']:
                        psk = payload['password']
                        subprocess.check_output(
                            """sed -i -e 's/wpa_passphrase=.*/wpa_passphrase={}/' {}""".format(psk, hostapd_file), shell=True)

                    def restart_ap0_interface():
                        import subprocess
                        import time
                        time.sleep(2)
                        subprocess.check_output('systemctl restart hostapd.service', shell=True)

                    # async restart hostapd service
                    thread = Thread(target=restart_ap0_interface)
                    thread.start()

                    return '', 204
                except Exception:
                    current_app.logger.error("ERROR: error occured in wireless setup:", sys.exc_info()[2])
                    current_app.logger.error(traceback.format_exc())
                    return 'Wireless Setup Failed!', 418
            else:
                current_app.logger.error("ERROR: invalid interface provided %s".format(payload['interface']))
                return 'Invalid Interface Provided - Setup Failed!', 418
        else:
            current_app.logger.error("ERROR: unsupported payload received %s".format(payload))
            return 'Invalid Setup Payload Received - Setup Failed!', 418
    else:
        if platform() == "RaspberryPi":
            return render_template_with_defaults('setup.html',
                hostname=hostname(),
                ap0=accesspoint_credentials(),
                wireless_credentials=wireless_credentials(),
                available_networks=available_networks())
        else:
            return render_template_with_defaults('setup.html',
                hostname=hostname(),
                ap0=None,
                wireless_credentials=None,
                available_networks=None)


def hostname():
    try:
        return subprocess.check_output("hostname", shell=True).decode("utf-8").strip()
    except Exception:
        current_app.logger.warn("current device doesn't support hostname changes")
    return None


def ip_addresses():
    command_output = None
    try:
        command_output = subprocess.check_output("ifconfig -l | xargs -n1 ipconfig getifaddr || hostname -I", shell=True).decode("utf-8").rstrip()
        command_output = list(filter(None, re.split('\\s', command_output)))
    except subprocess.CalledProcessError as error:
        # any interface that doesn't contain an IP address (bridges, etc) will error the `ipconfig getifaddr` command
        current_app.logger.warn(f"current device doesn't support 'ifconfig' error={error.returncode} output={error.output}")
        command_output = list(filter(None, re.split('\\s', error.output.decode())))

    pat = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    ip_addrs = [m.group(0) for s in command_output for m in pat.finditer(s)]

    if len(ip_addrs) > 0:
        return ip_addrs
    else:
        current_app.logger.warn(f"ip addresses weren't able to be discovered output={command_output}")
        # ip addresses weren't able to be gathered successfully
        return None


def accesspoint_credentials():
    # TODO: properly handle No such file or directory by hiding settings in /setup or showing error
    try:
        ssid = subprocess.check_output('more /etc/hostapd/hostapd.conf | grep -w ^ssid | awk -F "=" \'{print $2}\'', shell=True)
        psk = subprocess.check_output('more /etc/hostapd/hostapd.conf | grep -w ^wpa_passphrase | awk -F "=" \'{print $2}\'', shell=True)

        return {
            'ssid': ssid.decode("utf-8").strip().strip('"'),
            'psk': psk.decode("utf-8").strip().strip('"'),
        }
    except Exception:
        current_app.logger.warn("WARN: failed to retrieve access point information from hostapd")

    return {}


def wireless_credentials():
    # TODO: properly handle No such file or directory by hiding settings in /setup or showing error

    # grep -w matches an exact word:
    #   example non match:
    #       echo "bssid=test-value" | grep -w ssid => ""
    #   example match:
    #       echo "bssid=test-value" | grep -w bssid => "bssid=test-value"
    cmd_template = "more /etc/wpa_supplicant/wpa_supplicant-wlan0.conf | grep -v '^\s*[#]' | grep -w {key} "

    ssid = subprocess.check_output(cmd_template.format(key='ssid') + '| awk -F "=" \'{print $2}\'', shell=True)
    psk = subprocess.check_output(cmd_template.format(key='psk') + '| awk -F "=" \'{print $2}\'', shell=True)

    try:
        # first remove any line that might be a comment (default)
        # second filter to the line that contains the text 'bssid'
        # return the value after the '=' in bssid=<value>
        bssid = subprocess.check_output(cmd_template.format(key='bssid') + '| awk -F "=" \'{print $2}\'', shell=True)
    except Exception:
        bssid = None

    return {
        'ssid': ssid.decode("utf-8").strip().strip('"'),
        'psk': psk.decode("utf-8").strip().strip('"'),
        'bssid': bssid.decode("utf-8").strip().strip('"')
    }


@main.route('/about', methods=['GET'])
def about():
    # server_information: ip address and hostname
    server_information = {
        'hostname': hostname(),
        'ip_addresses': ip_addresses()
    }

    # query local git short sha
    gitSha = subprocess.check_output("cd {0}; git rev-parse --short HEAD".format(base_path()), shell=True)
    gitSha = gitSha.decode("utf-8")

    # query latest git remote sha
    try:
        latestMasterSha = subprocess.check_output("cd {0}; git fetch origin && git rev-parse --short origin/master".format(base_path()), shell=True)
        latestMasterSha = latestMasterSha.decode("utf-8")
    except Exception:
        latestMasterSha = "unavailable (check network)"

    # query for local file changes
    try:
        localChanges = subprocess.check_output("cd {0}; git fetch origin; git --no-pager diff --name-only".format(base_path()), shell=True)
        localChanges = localChanges.decode("utf-8").strip()
    except Exception:
        localChanges = "unavailable (check network)"

    # # capture raspbian pinout
    # proc = subprocess.Popen(["pinout"], stdout=subprocess.PIPE, shell=True)
    # (pinout, err) = proc.communicate()
    try:
        pinout = subprocess.check_output("pinout", shell=True)
        pinout = pinout.decode("utf-8")
    except Exception:
        pinout = None

    image_release = os.environ.get("IMG_RELEASE", None)
    image_variant = os.environ.get("IMG_VARIANT", None)
    image_version = None if image_release is None else f"{image_release}_{image_variant}"

    return render_template_with_defaults('about.html', git_version=gitSha, latest_git_sha=latestMasterSha, local_changes=localChanges,
                           server_info=server_information, os_release=system_info,
                           raspberrypi_info=pinout, raspberrypi_image=image_version)
