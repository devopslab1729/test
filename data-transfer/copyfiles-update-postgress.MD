Below is a **single, self-contained Python file** that does **batch-wise download from S3 → local → upload to SFTP → update PostgreSQL status**.

You can save this as **`s3_to_sftp_batch.py`** and run it directly.

Get s3 links from postgrss and copy file from s3 to local and upload to sftp server. update pregress in postgress with the status of the file copy and upload process.To achieve the task of copying files from S3 to local, uploading them to an SFTP server


Goal

Read S3 file URLs/keys from PostgreSQL
Download files from S3 → local
Upload files to an SFTP server
Update progress/status back in PostgreSQL (success / failure / retries)


---

## 1. Prerequisites

```bash
pip install boto3 psycopg2-binary paramiko
```

Runs on:

* EC2 (recommended – use IAM role for S3)
* VM / container

Uses:

* **Amazon Web Services S3**
* **PostgreSQL**
* SFTP

---

## 2. Single Python File (All-in-One)

```python
#!/usr/bin/env python3

import os
import boto3
import psycopg2
import paramiko
from contextlib import closing

# =========================
# CONFIGURATION
# =========================

BATCH_SIZE = 50
LOCAL_TMP_DIR = "/tmp/s3_files"

DB_CONFIG = {
    "host": "postgres-host",
    "dbname": "filesdb",
    "user": "dbuser",
    "password": "dbpassword",
    "port": 5432,
}

SFTP_CONFIG = {
    "host": "sftp.example.com",
    "port": 22,
    "username": "sftpuser",
    "password": "sftppassword",
    # "key_filename": "/path/to/private_key"  # preferred
}

SFTP_BASE_DIR = "/incoming"

os.makedirs(LOCAL_TMP_DIR, exist_ok=True)

# =========================
# AWS S3 CLIENT
# =========================

s3_client = boto3.client("s3")

# =========================
# DATABASE HELPERS
# =========================

def fetch_batch(conn, batch_size):
    """
    Fetch next batch of PENDING jobs and mark them IN_PROGRESS
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, s3_bucket, s3_key
            FROM file_transfer_jobs
            WHERE status = 'PENDING'
            ORDER BY id
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        """, (batch_size,))
        rows = cur.fetchall()

        if rows:
            job_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE file_transfer_jobs
                SET status = 'IN_PROGRESS', updated_at = now()
                WHERE id = ANY(%s)
            """, (job_ids,))
        conn.commit()

    return rows


def update_status(conn, job_id, status, error_message=None):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE file_transfer_jobs
            SET status = %s,
                error_message = %s,
                updated_at = now()
            WHERE id = %s
        """, (status, error_message, job_id))
    conn.commit()

# =========================
# S3 DOWNLOAD
# =========================

def download_from_s3(bucket, key, local_path):
    s3_client.download_file(bucket, key, local_path)

# =========================
# SFTP UPLOAD
# =========================

def sftp_connect():
    transport = paramiko.Transport((SFTP_CONFIG["host"], SFTP_CONFIG["port"]))
    transport.connect(
        username=SFTP_CONFIG["username"],
        password=SFTP_CONFIG.get("password"),
        # pkey=paramiko.RSAKey.from_private_key_file(SFTP_CONFIG["key_filename"])
    )
    return paramiko.SFTPClient.from_transport(transport), transport


def upload_to_sftp(sftp, local_file, remote_file):
    sftp.put(local_file, remote_file)

# =========================
# PROCESS SINGLE JOB
# =========================

def process_job(conn, sftp, job):
    job_id, bucket, key = job
    filename = os.path.basename(key)
    local_file = os.path.join(LOCAL_TMP_DIR, filename)
    remote_file = f"{SFTP_BASE_DIR}/{filename}"

    try:
        update_status(conn, job_id, "DOWNLOADING")
        download_from_s3(bucket, key, local_file)

        update_status(conn, job_id, "UPLOADING")
        upload_to_sftp(sftp, local_file, remote_file)

        update_status(conn, job_id, "SUCCESS")
        os.remove(local_file)

    except Exception as e:
        update_status(conn, job_id, "FAILED", str(e))
        if os.path.exists(local_file):
            os.remove(local_file)

# =========================
# MAIN BATCH LOOP
# =========================

def main():
    print("Starting batch file transfer job")

    with closing(psycopg2.connect(**DB_CONFIG)) as conn:
        while True:
            batch = fetch_batch(conn, BATCH_SIZE)

            if not batch:
                print("No more pending files.")
                break

            print(f"Processing batch of {len(batch)} files")

            sftp, transport = sftp_connect()

            try:
                for job in batch:
                    process_job(conn, sftp, job)
            finally:
                sftp.close()
                transport.close()

    print("All batches completed.")

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()
```

---

## 3. Status Lifecycle (Per File)

```
PENDING
  ↓
IN_PROGRESS
  ↓
DOWNLOADING
  ↓
UPLOADING
  ↓
SUCCESS / FAILED
```

---

