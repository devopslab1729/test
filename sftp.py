import boto3
import paramiko
import os
import io
import json
import socket

s3 = boto3.client('s3')
secrets = boto3.client('secretsmanager')

def lambda_handler(event, context):
    print("Event:", event)

    # 1. Read S3 details
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    file_name = os.path.basename(key)
    tmp_path = f"/tmp/{file_name}"

    # 2. Download S3 file to Lambda /tmp
    s3.download_file(bucket, key, tmp_path)
    print(f"Downloaded S3 file to {tmp_path}")

    # 3. Load private key
    private_key_path = "/path/to/key.pem"
    key_obj = paramiko.RSAKey.from_private_key_file(private_key_path)



    # 4. SFTP connection info
    SFTP_HOST = "sftp.example.com"
    SFTP_PORT = 22
    SFTP_USER = "sftpuser"
    REMOTE_PATH = f"/upload/{file_name}"

    # 5. Connect to SFTP
    # Create a socket and Transport so we can adjust Paramiko security options
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((SFTP_HOST, SFTP_PORT))
    transport = paramiko.Transport(sock)

    # Adjust security options to permit legacy DSA host/key algorithm `ssh-dss` if needed.
    # Note: enabling `ssh-dss` reduces security; prefer upgrading the server to modern keys.
    try:
        sec = transport.get_security_options()

        # Best-effort: if the SecurityOptions object exposes `preferred_keys`, prepend `ssh-dss`.
        # Otherwise, try removing `ssh-dss` from the `disabled_algorithms` dict.
        try:
            current = getattr(sec, 'preferred_keys', None)
            if current:
                # Ensure we don't duplicate
                pref = tuple(current)
                if 'ssh-dss' not in pref:
                    sec.preferred_keys = ('ssh-dss',) + pref
            else:
                sec.preferred_keys = ('ssh-dss',)
        except Exception:
            da = getattr(sec, 'disabled_algorithms', None)
            if isinstance(da, dict):
                keys_disabled = da.get('keys', [])
                if 'ssh-dss' in keys_disabled:
                    keys_disabled = [k for k in keys_disabled if k != 'ssh-dss']
                    da['keys'] = keys_disabled
                    # assign back in case the implementation requires it
                    sec.disabled_algorithms = da
    except Exception as e:
        print("Warning: could not adjust Paramiko security options:", e)

    transport.connect(username=SFTP_USER, pkey=key_obj)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # 6. Upload
    sftp.put(tmp_path, REMOTE_PATH)
    print(f"Uploaded file to {REMOTE_PATH}")

    sftp.close()
    transport.close()

    return {"status": "success"}
