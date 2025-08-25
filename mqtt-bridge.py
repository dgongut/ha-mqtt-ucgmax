import paramiko
import paho.mqtt.client as mqtt
import time
import json
from datetime import datetime
from config import *

def debug(message):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - DEBUG: {message}')

def error(message):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - ERROR: {message}')

def warning(message):
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - WARNING: {message}')

MQTT_TOPIC_PERCENTAGE_STATE = "ucgmax/ventilador/percentage_state"
MQTT_TOPIC_PERCENTAGE_SET = "ucgmax/ventilador/percentage_set"
MQTT_TOPIC_POWER_STATE = "ucgmax/ventilador/power_state"
MQTT_TOPIC_POWER_SET = "ucgmax/ventilador/power_set"
MQTT_TOPIC_AVAIL = "ucgmax/ventilador/availability"

# ===========================
# Timings
# ===========================
READ_PERIOD_S = 1.0
HEARTBEAT_S = 5.0

# ===========================
# Conexión SSH
# ===========================
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
debug(f"Conectando a {UCG_MAX_IP}:{UCG_MAX_SSH_PORT} como {UCG_MAX_SSH_USER}...")
debug(f"Usando clave SSH en {UCG_MAX_SSH_KEY_PATH}")
ssh.connect(UCG_MAX_IP, port=UCG_MAX_SSH_PORT, username=UCG_MAX_SSH_USER, key_filename=UCG_MAX_SSH_KEY_PATH)

# ===========================
# Variables de estado
# ===========================
ultimo_porcentaje_publicado = None
ultimo_estado_power = None
ultimo_publish_ts = 0.0

# ===========================
# Funciones auxiliares
# ===========================
def pwm_to_percentage(valor_pwm: int) -> int:
    return round((valor_pwm / 255) * 100)

def percentage_to_pwm(porcentaje: int) -> int:
    return round((porcentaje / 100) * 255)

# ===========================
# Callbacks MQTT
# ===========================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        debug("Conectado a MQTT correctamente (v2)")
        client.subscribe(MQTT_TOPIC_PERCENTAGE_SET)
        client.subscribe(MQTT_TOPIC_POWER_SET)

        # Publicar disponibilidad
        client.publish(MQTT_TOPIC_AVAIL, "online", retain=True)

        # Enviar configuración de discovery para HA
        discovery_topic = f"{HA_DISCOVERY_PREFIX}/fan/ucgmax/config"
        discovery_payload = {
            "name": HA_ENTITY_NAME,
            "unique_id": HA_ENTITY_ID,
            "availability_topic": MQTT_TOPIC_AVAIL,
            "command_topic": MQTT_TOPIC_POWER_SET,
            "state_topic": MQTT_TOPIC_POWER_STATE,
            "percentage_command_topic": MQTT_TOPIC_PERCENTAGE_SET,
            "percentage_state_topic": MQTT_TOPIC_PERCENTAGE_STATE,
            "speed_range_min": 1,
            "speed_range_max": 100,
            "payload_on": "ON",
            "payload_off": "OFF"
        }
        client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)

    else:
        error("Error de conexión MQTT, código:", reason_code)

def on_message(client, userdata, msg):
    global ultimo_porcentaje_publicado, ultimo_estado_power

    try:
        if msg.topic == MQTT_TOPIC_POWER_SET:
            comando = msg.payload.decode().upper()
            if comando == "OFF":
                ssh.exec_command(f"echo 0 > {PWM_FILE}")
                ultimo_porcentaje_publicado = 0
                ultimo_estado_power = "OFF"
                client.publish(MQTT_TOPIC_POWER_STATE, "OFF", retain=True)
                client.publish(MQTT_TOPIC_PERCENTAGE_STATE, "0", retain=True)
                debug("Ventilador apagado")
            elif comando == "ON":
                # Si se enciende sin porcentaje, usar último conocido o 100
                porcentaje = ultimo_porcentaje_publicado if ultimo_porcentaje_publicado and ultimo_porcentaje_publicado > 0 else 100
                pwm = percentage_to_pwm(porcentaje)
                ssh.exec_command(f"echo {pwm} > {PWM_FILE}")
                ultimo_porcentaje_publicado = porcentaje
                ultimo_estado_power = "ON"
                client.publish(MQTT_TOPIC_POWER_STATE, "ON", retain=True)
                client.publish(MQTT_TOPIC_PERCENTAGE_STATE, str(porcentaje), retain=True)
                debug(f"Ventilador encendido a {porcentaje}%")

        elif msg.topic == MQTT_TOPIC_PERCENTAGE_SET:
            porcentaje = int(msg.payload.decode())
            if porcentaje <= 0:
                ssh.exec_command(f"echo 0 > {PWM_FILE}")
                ultimo_porcentaje_publicado = 0
                ultimo_estado_power = "OFF"
                client.publish(MQTT_TOPIC_POWER_STATE, "OFF", retain=True)
                client.publish(MQTT_TOPIC_PERCENTAGE_STATE, "0", retain=True)
                debug("Ventilador apagado por porcentaje=0")
            else:
                pwm = percentage_to_pwm(porcentaje)
                ssh.exec_command(f"echo {pwm} > {PWM_FILE}")
                ultimo_porcentaje_publicado = porcentaje
                ultimo_estado_power = "ON"
                client.publish(MQTT_TOPIC_POWER_STATE, "ON", retain=True)
                client.publish(MQTT_TOPIC_PERCENTAGE_STATE, str(porcentaje), retain=True)
                debug(f"Velocidad cambiada a {porcentaje}%")

    except Exception as e:
        error("Error en on_message:", e)

# ===========================
# Configuración cliente MQTT (API v2)
# ===========================
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
client.username_pw_set(MQTT_BROKER_USER, MQTT_BROKER_PASS)
client.on_connect = on_connect
client.on_message = on_message

client.will_set(MQTT_TOPIC_AVAIL, "offline", retain=True)

client.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)
client.loop_start()

# ===========================
# Loop principal
# ===========================
try:
    while True:
        stdin, stdout, stderr = ssh.exec_command(f"cat {PWM_FILE}")
        valor = stdout.read().decode().strip()

        if valor.isdigit():
            pwm_val = int(valor)
            porcentaje = pwm_to_percentage(pwm_val)
            estado_power = "ON" if porcentaje > 0 else "OFF"

            ahora = time.time()

            if porcentaje != ultimo_porcentaje_publicado or (ahora - ultimo_publish_ts) > HEARTBEAT_S:
                client.publish(MQTT_TOPIC_PERCENTAGE_STATE, str(porcentaje), retain=True)
                ultimo_porcentaje_publicado = porcentaje
                ultimo_publish_ts = ahora

            if estado_power != ultimo_estado_power:
                client.publish(MQTT_TOPIC_POWER_STATE, estado_power, retain=True)
                ultimo_estado_power = estado_power

        time.sleep(READ_PERIOD_S)

except KeyboardInterrupt:
    warning("Cerrando conexión...")
    ssh.close()
    client.loop_stop()