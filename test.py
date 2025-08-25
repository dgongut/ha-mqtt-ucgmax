import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(
    "10.0.10.1",  # reemplaza con tu UCG_MAX_IP
    username="ui",
    key_filename="/app/config/id_rsa"
)

stdin, stdout, stderr = ssh.exec_command("cat /sys/class/hwmon/hwmon0/pwm1")
print(stdout.read().decode())