import os

UCG_MAX_IP = str(os.environ.get("UCG_MAX_IP", ""))
UCG_MAX_SSH_PORT = int(os.environ.get("UCG_MAX_SSH_PORT", 22))
UCG_MAX_SSH_USER = str(os.environ.get("UCG_MAX_SSH_USER", "ui"))
MQTT_BROKER_IP = str(os.environ.get("MQTT_BROKER_IP", ""))
MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883))
MQTT_BROKER_USER = str(os.environ.get("MQTT_BROKER_USER", ""))
MQTT_BROKER_PASS = str(os.environ.get("MQTT_BROKER_PASS", ""))
HA_DISCOVERY_PREFIX = str(os.environ.get("HA_DISCOVERY_PREFIX", "homeassistant"))
HA_ENTITY_NAME = str(os.environ.get("HA_ENTITY_NAME", "Ventilador UCG-Max"))
HA_ENTITY_ID = str(os.environ.get("HA_ENTITY_ID", "ucgmax_ventilador"))
UCG_MAX_SSH_KEY_PATH = "/app/config/id_rsa"
PWM_FILE = "/sys/class/hwmon/hwmon0/pwm1"