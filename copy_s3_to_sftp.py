import boto3
import paramiko
import os
import io
import json

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
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, pkey=key_obj)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # 6. Upload
    sftp.put(tmp_path, REMOTE_PATH)
    print(f"Uploaded file to {REMOTE_PATH}")

    sftp.close()
    transport.close()

    return {"status": "success"}
