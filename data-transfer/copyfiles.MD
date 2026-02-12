To **copy files from S3 to an SFTP server and verify checksums**, you can follow this clean and reliable approach.

---

# ✅ Recommended Method (Step-by-Step)

## 1️⃣ Download files from S3

Use AWS CLI:

```bash
aws s3 cp s3://my-bucket/my-folder/ /tmp/my-folder/ --recursive
```

Or sync:

```bash
aws s3 sync s3://my-bucket/my-folder/ /tmp/my-folder/
```

---

## 2️⃣ Generate checksums (before transfer)

Generate SHA256 checksums for all files:

```bash
cd /tmp/my-folder
find . -type f -exec sha256sum {} \; > checksums_before.txt
```

---

## 3️⃣ Copy files to SFTP server

Using `scp`:

```bash
scp -i mykey.pem -r /tmp/my-folder user@sftp-server:/remote/path/
```

Or using `sftp` batch mode:

```bash
sftp -i mykey.pem user@sftp-server <<EOF
cd /remote/path
put -r /tmp/my-folder
bye
EOF
```

---

## 4️⃣ Verify checksums on SFTP server

SSH into SFTP server:

```bash
ssh -i mykey.pem user@sftp-server
```

Then:

```bash
cd /remote/path/my-folder
find . -type f -exec sha256sum {} \; > checksums_after.txt
```

---

## 5️⃣ Compare checksums

Back on local machine:

```bash
diff checksums_before.txt checksums_after.txt
```

If no output → ✅ Files match.

---

# 🔥 Better Automated Script (Production Style)

Here’s a simple bash script:

```bash
#!/bin/bash

BUCKET="my-bucket"
PREFIX="my-folder"
LOCAL_DIR="/tmp/my-folder"
REMOTE_USER="user"
REMOTE_HOST="sftp-server"
REMOTE_DIR="/remote/path"
KEY="mykey.pem"

# Download
aws s3 sync s3://$BUCKET/$PREFIX $LOCAL_DIR

# Generate checksum before
cd $LOCAL_DIR
find . -type f -exec sha256sum {} \; | sort > /tmp/checksums_before.txt

# Copy to SFTP
scp -i $KEY -r $LOCAL_DIR $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR

# Generate checksum on remote
ssh -i $KEY $REMOTE_USER@$REMOTE_HOST "
cd $REMOTE_DIR/$PREFIX
find . -type f -exec sha256sum {} \; | sort > /tmp/checksums_after.txt
"

# Fetch remote checksum file
scp -i $KEY $REMOTE_USER@$REMOTE_HOST:/tmp/checksums_after.txt /tmp/

# Compare
diff /tmp/checksums_before.txt /tmp/checksums_after.txt

if [ $? -eq 0 ]; then
  echo "✅ Transfer verified successfully"
else
  echo "❌ Checksum mismatch!"
fi
```

---

# 🚀 Enterprise Option (Direct Streaming Without Local Storage)

If files are large and you don’t want local disk usage:

```bash
aws s3 cp s3://my-bucket/file.txt - | \
ssh user@sftp-server "cat > /remote/path/file.txt"
```

Then verify checksum manually.

---

# 🔐 Important Notes

* Use **sha256sum** (better than md5)
* Always `sort` checksum output before diff
* For large datasets, consider `rsync -avz --progress`
* If using AWS KMS encrypted files → AWS CLI handles decryption automatically

---

# 🎯 Best Practice (Recommended for Production)

If possible, use:

```
aws s3 sync → rsync over SSH → compare checksums
```

`rsync` can verify with checksum mode:

```bash
rsync -avc -e "ssh -i mykey.pem" /tmp/my-folder/ user@sftp-server:/remote/path/
```

`-c` forces checksum verification.

---

If you want, tell me:

* Is this running from EC2?
* Are files large (GBs/TBs)?
* Is this one-time or scheduled job?

I can give you a more optimized production-ready solution.


Perfect 👍 Since this runs from **EC2**, we can make it cleaner, secure, and production-ready.

Assumptions:

* EC2 has an **IAM Role** attached (no AWS keys needed)
* EC2 can reach SFTP server over port 22
* Using SSH private key for SFTP auth

---

# ✅ Production-Ready Script (EC2 → S3 → SFTP + Checksum Validation)

This script:

* Syncs from S3
* Generates SHA256 checksums
* Transfers using rsync (faster + resumable)
* Validates checksums on remote
* Fails properly if mismatch

---

## 📜 `s3_to_sftp_with_checksum.sh`

```bash
#!/bin/bash
set -euo pipefail

### CONFIG ###
BUCKET="my-bucket"
PREFIX="my-folder"
LOCAL_DIR="/tmp/my-folder"
REMOTE_USER="user"
REMOTE_HOST="sftp.example.com"
REMOTE_DIR="/remote/path"
SSH_KEY="/home/ec2-user/.ssh/sftp_key.pem"

LOG_FILE="/var/log/s3_sftp_transfer.log"

echo "===== Transfer Started at $(date) =====" | tee -a $LOG_FILE

# 1️⃣ Sync from S3
echo "Syncing from S3..." | tee -a $LOG_FILE
aws s3 sync s3://$BUCKET/$PREFIX $LOCAL_DIR --delete | tee -a $LOG_FILE

# 2️⃣ Generate local checksums
echo "Generating local checksums..." | tee -a $LOG_FILE
cd $LOCAL_DIR
find . -type f -exec sha256sum {} \; | sort > /tmp/checksums_before.txt

# 3️⃣ Transfer using rsync (better than scp)
echo "Transferring files to SFTP..." | tee -a $LOG_FILE
rsync -avz --progress \
    -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
    $LOCAL_DIR/ \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/ | tee -a $LOG_FILE

# 4️⃣ Generate remote checksums
echo "Generating remote checksums..." | tee -a $LOG_FILE
ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST "
cd $REMOTE_DIR
find . -type f -exec sha256sum {} \; | sort > /tmp/checksums_after.txt
"

# 5️⃣ Copy remote checksum file back
scp -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST:/tmp/checksums_after.txt /tmp/

# 6️⃣ Compare checksums
echo "Comparing checksums..." | tee -a $LOG_FILE
if diff /tmp/checksums_before.txt /tmp/checksums_after.txt > /dev/null; then
    echo "✅ Transfer verified successfully" | tee -a $LOG_FILE
else
    echo "❌ Checksum mismatch detected!" | tee -a $LOG_FILE
    exit 1
fi

echo "===== Transfer Completed at $(date) =====" | tee -a $LOG_FILE
```

---

# 🔐 EC2 Best Practices

### 1️⃣ Use IAM Role (NOT access keys)

Attach policy:

```json
{
  "Effect": "Allow",
  "Action": ["s3:ListBucket", "s3:GetObject"],
  "Resource": [
    "arn:aws:s3:::my-bucket",
    "arn:aws:s3:::my-bucket/*"
  ]
}
```

---

### 2️⃣ Secure SSH Key

```bash
chmod 400 ~/.ssh/sftp_key.pem
```

---

### 3️⃣ Schedule with Cron (if needed)

```bash
crontab -e
```

Example (run every night 2 AM):

```
0 2 * * * /home/ec2-user/s3_to_sftp_with_checksum.sh
```

---

# 🚀 If Files Are Very Large (100GB+)

Instead of generating separate checksum files, use:

```bash
rsync -avc -e "ssh -i key.pem" $LOCAL_DIR/ user@host:$REMOTE_DIR/
```

`-c` makes rsync verify via checksum automatically.

⚠ Slower but avoids separate diff step.

---

# 🔥 Enterprise Improvement Option

If you want **no local storage usage**, we can:

* Stream file-by-file from S3
* Calculate checksum during stream
* Upload directly

Let me know file sizes and count — I can optimize further.

---

Are:

* Files large (GBs)?
* Thousands of small files?
* Need parallel transfer?

Tell me your workload size — I’ll tune it properly for performance.

