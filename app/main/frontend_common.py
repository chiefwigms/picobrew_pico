import subprocess
from flask import render_template


def system_info():
    try:
        system_info = subprocess.check_output("cat /etc/os-release || sw_vers || systeminfo | findstr /C:'OS'", shell=True)
        system_info = system_info.decode("utf-8")
    except:
        system_info = "Not Supported on this Device"

    return system_info


# memorize system information
system_info = system_info()


def platform():
    system = system_info
    if 'raspbian' in system:
        return 'RaspberryPi'
    elif 'Mac OS X' in system:
        return 'MacOS'
    elif 'Microsoft Windows' in system:
        return 'Windows'
    else:
        return "unknown"


# memorize platform information
platform_info = platform()


def render_template_with_defaults(template, **kwargs):
    return render_template(template, platform=platform_info, **kwargs)
