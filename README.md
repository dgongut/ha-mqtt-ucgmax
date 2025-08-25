# ha-mqtt-ucgmax
Expone una entidad ventilador en Home Assistant que controlará el ventilador del UCG-Max a través de MQTT

¿Lo buscas en [![](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/dgongut/ha-mqtt-ucgmax)?

## Configuración en las variables del Docker Compose

| CLAVE  | OBLIGATORIO | VALOR |
|:------------- |:---------------:| :-------------|
| UCG_MAX_IP |✅| IP o hostname del host donde está el ventilador |
| UCG_MAX_SSH_PORT |❌| Puerto SSH del host remoto. Por defecto 22 |
| UCG_MAX_SSH_USER |✅| Usuario SSH en el host remoto |
| MQTT_BROKER_IP |✅| IP o hostname del broker MQTT |
| MQTT_BROKER_PORT |❌| Puerto del broker MQTT. Por defecto 1883 |
| MQTT_BROKER_USER |✅| Usuario MQTT |
| MQTT_BROKER_PASS |✅| Contraseña MQTT |
| HA_DISCOVERY_PREFIX |❌| Prefijo para MQTT discovery en Home Assistant. Por defecto `homeassistant` |
| HA_ENTITY_NAME |❌| Nombre de la entidad fan en Home Assistant. Por defecto `Ventilador UCG-Max` |
| HA_ENTITY_ID |❌| ID único de la entidad en Home Assistant. Por defecto `ucgmax_ventilador` |
| TZ |✅| Timezone (Por ejemplo `Europe/Madrid`) |

## 
> [!WARNING]
> Será necesario mapear un volumen para la clave SSH: /path/en/host/id_rsa:/app/config/id_rsa:ro

##
> [!WARNING]
> Será necesario haber habilitado el SSH en el UCG-Max

##
> [!WARNING]
> Será necesario tener la integración de MQTT instalada en Home Assistant escuchando en el topic ID con el prefijo que le pongáis en `HA_DISCOVERY_PREFIX` en el Docker-Compose

## Cómo generar la clave SSH para el contenedor

1. Genera una clave nueva en tu máquina:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_ucgmax
```

2. Copia la clave pública al host donde está el ventilador:
```bash
ssh-copy-id -i ~/.ssh/id_rsa_ucgmax.pub ui@UCG_MAX_IP
```

3. Monta la clave privada en el contenedor:
```yaml
volumes:
  - /home/usuario/.ssh/id_rsa_ucgmax:/app/config/id_rsa:ro
```
:ro → solo lectura, más seguro

4. Verifica la conexión desde el contenedor (opcional pero muy recomendado, solo funcionará si ya se ha ejecutado el docker-compose):
```bash
docker exec -it ha-mqtt-ucgmax ssh -i /root/.ssh/id_rsa ui@UCG_MAX_IP "cat /sys/class/hwmon/hwmon0/pwm1"
```

## Ejemplo de Docker-Compose

```yaml
services:
    ha-mqtt-ucgmax:
        environment:
            - UCG_MAX_IP=
            - UCG_MAX_SSH_PORT=22
            - UCG_MAX_SSH_USER=ui
            - MQTT_BROKER_IP=
            - MQTT_BROKER_PORT=1883
            - MQTT_BROKER_USER=admin
            - MQTT_BROKER_PASS=
            - HA_DISCOVERY_PREFIX=homeassistant
            - HA_ENTITY_NAME=Ventilador UCG-Max
            - HA_ENTITY_ID=ucgmax_ventilador
            - TZ=Europe/Madrid
        volumes:
            - /home/usuario/.ssh/id_rsa:/app/config/id_rsa:ro
        image: dgongut/ha-mqtt-ucgmax:latest
        container_name: ha-mqtt-ucgmax
        restart: always
        network_mode: bridge
        tty: true
```