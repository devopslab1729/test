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
