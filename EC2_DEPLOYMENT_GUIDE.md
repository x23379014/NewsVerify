# EC2 Deployment Guide - NewsVerify

Complete guide to deploy NewsVerify directly to an EC2 instance.

---

## Prerequisites

- AWS Account
- AWS CLI configured
- SSH key pair (or create one)
- Model files uploaded to S3

---

## Step 1: Create EC2 Instance

### Option A: Using AWS Console

1. Go to [EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click **Launch Instance**
3. Configure:
   - **Name**: `newsverify-server`
   - **AMI**: Amazon Linux 2023 (or Ubuntu 22.04 LTS)
   - **Instance type**: `t3.medium` or `t3.large` (recommended for ML models)
   - **Key pair**: Create new or select existing
   - **Network settings**: 
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere (0.0.0.0/0)
     - Allow HTTPS (port 443) from anywhere (optional)
   - **Storage**: 20 GB (minimum)
4. Click **Launch Instance**

### Option B: Using AWS CLI

```bash
# Create security group first
aws ec2 create-security-group \
    --group-name newsverify-sg \
    --description "Security group for NewsVerify application"

# Get your public IP (for SSH access)
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
    --group-name newsverify-sg \
    --protocol tcp \
    --port 22 \
    --cidr $MY_IP/32

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
    --group-name newsverify-sg \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name your-key-name \
    --security-groups newsverify-sg \
    --user-data file://ec2-setup.sh
```

---

## Step 2: Create IAM Role for EC2

The EC2 instance needs permissions to access S3.

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Roles** → **Create role**
3. Select **AWS service** → **EC2**
4. Attach policies:
   - `AmazonS3ReadOnlyAccess` (or custom policy for your bucket)
   - `CloudWatchLogsFullAccess`
5. Role name: `NewsVerify-EC2-Role`
6. Click **Create role**

**Custom S3 Policy (if needed):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::newsverify-models-2026",
        "arn:aws:s3:::newsverify-models-2026/*"
      ]
    }
  ]
}
```

### Attach Role to EC2 Instance

1. Go to EC2 Console
2. Select your instance
3. Click **Actions** → **Security** → **Modify IAM role**
4. Select `NewsVerify-EC2-Role`
5. Click **Update IAM role**

---

## Step 3: Connect to EC2 Instance

### Get Instance Details

```bash
# Get public IP
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=newsverify-server" \
    --query "Reservations[*].Instances[*].PublicIpAddress" \
    --output text
```

### SSH into Instance

**For Amazon Linux:**
```bash
ssh -i your-key.pem ec2-user@<PUBLIC_IP>
```

**For Ubuntu:**
```bash
ssh -i your-key.pem ubuntu@<PUBLIC_IP>
```

---

## Step 4: Set Up Environment on EC2

### Update System (Amazon Linux)

```bash
# Update system
sudo yum update -y

# Install Python 3.9 and pip
sudo yum install -y python3.9 python3.9-pip git

# Install development tools
sudo yum groupinstall -y "Development Tools"
```

### Update System (Ubuntu)

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.9 and pip
sudo apt-get install -y python3.9 python3.9-pip python3.9-venv git build-essential
```

---

## Step 5: Clone and Set Up Application

```bash
# Create application directory
mkdir -p /home/ec2-user/newsverify
cd /home/ec2-user/newsverify

# Option 1: Clone from GitHub (if you've pushed to GitHub)
git clone https://github.com/YOUR_USERNAME/NewsVerify.git .

# Option 2: Upload files using SCP (from your local machine)
# Run this from your local machine:
# scp -i your-key.pem -r /Users/nikhiltamatta/Desktop/NewsVerify/* ec2-user@<PUBLIC_IP>:/home/ec2-user/newsverify/
```

### Create Virtual Environment

```bash
# Create virtual environment
python3.9 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

---

## Step 6: Configure Environment Variables

```bash
# Create .env file
cat > /home/ec2-user/newsverify/.env << EOF
S3_BUCKET=newsverify-models-2026
MODEL_KEY=models/model.pkl
VECTORIZER_KEY=models/tfidf_vectorizer.pkl
LABEL_ENCODER_KEY=models/label_encoder.pkl
STAT_FEATURES_KEY=models/stat_feature_names.pkl
AWS_DEFAULT_REGION=us-east-1
FLASK_ENV=production
EOF
```

Or export them:
```bash
export S3_BUCKET=newsverify-models-2026
export MODEL_KEY=models/model.pkl
export VECTORIZER_KEY=models/tfidf_vectorizer.pkl
export LABEL_ENCODER_KEY=models/label_encoder.pkl
export STAT_FEATURES_KEY=models/stat_feature_names.pkl
export AWS_DEFAULT_REGION=us-east-1
```

---

## Step 7: Test Application Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Test if application runs
python application.py
```

Press `Ctrl+C` to stop. If it works, proceed to next step.

---

## Step 8: Set Up Gunicorn and Nginx

### Install Gunicorn (if not in requirements.txt)

```bash
source venv/bin/activate
pip install gunicorn
```

### Create Gunicorn Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/newsverify.service
```

Add this content:
```ini
[Unit]
Description=NewsVerify Gunicorn Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/newsverify
Environment="PATH=/home/ec2-user/newsverify/venv/bin"
Environment="S3_BUCKET=newsverify-models-2026"
Environment="MODEL_KEY=models/model.pkl"
Environment="VECTORIZER_KEY=models/tfidf_vectorizer.pkl"
Environment="LABEL_ENCODER_KEY=models/label_encoder.pkl"
Environment="STAT_FEATURES_KEY=models/stat_feature_names.pkl"
Environment="AWS_DEFAULT_REGION=us-east-1"
ExecStart=/home/ec2-user/newsverify/venv/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:5000 \
    --timeout 120 \
    application:application

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, then Y, then Enter).

### Start Gunicorn Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable newsverify

# Start service
sudo systemctl start newsverify

# Check status
sudo systemctl status newsverify

# View logs
sudo journalctl -u newsverify -f
```

---

## Step 9: Install and Configure Nginx

### Install Nginx

**Amazon Linux:**
```bash
sudo amazon-linux-extras install nginx1 -y
```

**Ubuntu:**
```bash
sudo apt-get install -y nginx
```

### Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/conf.d/newsverify.conf
```

Add this content:
```nginx
server {
    listen 80;
    server_name _;  # Replace with your domain if you have one

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # Static files (if needed)
    location /static {
        alias /home/ec2-user/newsverify/app/static;
    }
}
```

### Start Nginx

```bash
# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx

# Enable Nginx (start on boot)
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

---

## Step 10: Test Application

```bash
# Get your public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Test health endpoint
curl http://<PUBLIC_IP>/health

# Test prediction
curl -X POST http://<PUBLIC_IP>/predict \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Scientists discover new planet",
    "body": "Amazing discovery...",
    "url": "https://example.com"
  }'
```

---

## Step 11: Set Up Auto-Start on Reboot

The systemd service should already auto-start, but verify:

```bash
# Check if service is enabled
sudo systemctl is-enabled newsverify

# If not enabled, enable it
sudo systemctl enable newsverify
```

---

## Useful Commands

### View Application Logs

```bash
# Gunicorn logs
sudo journalctl -u newsverify -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs (if logging to file)
tail -f /home/ec2-user/newsverify/app.log
```

### Restart Services

```bash
# Restart application
sudo systemctl restart newsverify

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status newsverify
sudo systemctl status nginx
```

### Update Application

```bash
cd /home/ec2-user/newsverify

# Pull latest changes (if using Git)
git pull

# Or upload new files via SCP
# From local machine:
# scp -i your-key.pem -r /path/to/files/* ec2-user@<IP>:/home/ec2-user/newsverify/

# Restart service
sudo systemctl restart newsverify
```

---

## Troubleshooting

### Issue: Application Not Starting

**Check logs:**
```bash
sudo journalctl -u newsverify -n 50
```

**Common fixes:**
- Check environment variables are set
- Verify model files exist in S3
- Check IAM role has S3 permissions

### Issue: 502 Bad Gateway

**Causes:**
- Gunicorn not running
- Wrong port in Nginx config
- Application crashed

**Fix:**
```bash
# Check Gunicorn is running
sudo systemctl status newsverify

# Check Nginx config
sudo nginx -t

# Restart both
sudo systemctl restart newsverify
sudo systemctl restart nginx
```

### Issue: Can't Access from Browser

**Check:**
1. Security group allows HTTP (port 80)
2. Nginx is running: `sudo systemctl status nginx`
3. Application is running: `sudo systemctl status newsverify`

### Issue: Model Not Loading

**Check:**
1. IAM role attached to instance
2. S3 bucket name correct
3. Model files exist in S3:
   ```bash
   aws s3 ls s3://newsverify-models-2026/models/
   ```

---

## Security Best Practices

1. **Use HTTPS**: Set up SSL certificate with Let's Encrypt
2. **Firewall**: Only open necessary ports
3. **SSH Keys**: Use key pairs, disable password login
4. **Regular Updates**: Keep system and packages updated
5. **Backup**: Regularly backup application and data

---

## Cost Optimization

- **Stop instance** when not in use:
  ```bash
  aws ec2 stop-instances --instance-ids i-xxxxx
  ```

- **Use smaller instance** for development (t3.small)
- **Reserved Instances** for production (save ~30-40%)

**Estimated Monthly Cost:**
- t3.medium: ~$30/month
- t3.large: ~$60/month

---

## Next Steps

1. **Custom Domain**: Point domain to EC2 public IP
2. **HTTPS**: Set up SSL with Let's Encrypt
3. **Monitoring**: Set up CloudWatch alarms
4. **Auto-scaling**: Use Auto Scaling Groups (if needed)
5. **Load Balancing**: Add Application Load Balancer (if needed)

---

## Quick Reference

**Your Configuration:**
- Instance: t3.medium (or t3.large)
- Application: `/home/ec2-user/newsverify`
- Gunicorn: Port 5000 (internal)
- Nginx: Port 80 (external)
- S3 Bucket: `newsverify-models-2026`
- IAM Role: `NewsVerify-EC2-Role`

**Important Files:**
- Service: `/etc/systemd/system/newsverify.service`
- Nginx: `/etc/nginx/conf.d/newsverify.conf`
- App: `/home/ec2-user/newsverify/`

---

**Good luck with your deployment! 🚀**
