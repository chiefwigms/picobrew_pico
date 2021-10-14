from flask import current_app
import requests
import shutil
import json

from .config import (MachineType, brew_archive_sessions_path, ferm_archive_sessions_path,
                     still_archive_sessions_path, iSpindel_archive_sessions_path, tilt_archive_sessions_path)


def send_webhook(webhook, message):
    if not webhook.enabled:
        return

    try:
        response = requests.post(webhook.url,
                                 data=json.dumps(
                                     message, sort_keys=True, default=str),
                                 headers={'Content-Type': 'application/json'},
                                 timeout=1.0)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        current_app.logger.error(f'error received while processing webhook {webhook.url} : {err}')
        webhook.status = "error"
        pass
    except requests.exceptions.ConnectionError as err:
        current_app.logger.error(f'webhook destination failed to establish a connection {webhook.url} : {err}')
        webhook.status = "error"
        pass
    except requests.exceptions.Timeout as err:
        current_app.logger.error(f'timeout occured while processing webhook {webhook.url} : {err}')
        webhook.status = "error"
        pass
    except requests.exceptions.RequestException as err:
        current_app.logger.error(f'unknown error occured while processing webhook {webhook.url} : {err}')
        webhook.status = "error"
        pass
    except:
        webhook.status = "error"
        pass
    else:
        webhook.status = "success"
        return response.status_code