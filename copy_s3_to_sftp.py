import boto3
import paramiko
import os

s3 = boto3.client('s3')

def copy_s3_to_sftp():

    bucket = "my-bucket"
    key = "folder/data.txt"

    # Download from S3 to /tmp
    local_file = f"/tmp/{os.path.basename(key)}"
    s3.download_file(bucket, key, local_file)

    # Load private key
    private_key_path = "/path/to/key.pem"
    key_obj = paramiko.RSAKey.from_private_key_file(private_key_path)

    # SFTP details
    host = "sftp.server.com"
    username = "sftpuser"
    port = 22

    # Connect
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, pkey=key_obj)

    sftp = paramiko.SFTPClient.from_transport(transport)

    # Upload file
    sftp.put(local_file, "/incoming/data.txt")

    sftp.close()
    transport.close()

    print("Upload completed")
