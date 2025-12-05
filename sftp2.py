import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Allow DSS host keys
paramiko.transport.Transport._preferred_kex = (
    'diffie-hellman-group1-sha1',
    'diffie-hellman-group14-sha1'
)
paramiko.transport.Transport._preferred_keys = (
    'ssh-dss',
)

client.connect(
    hostname="your-host",
    username="user",
    password="pass",
    allow_agent=False,
    look_for_keys=False
)
