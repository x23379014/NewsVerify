# Complete Setup Guide - NewsVerify

This is your complete step-by-step guide for setting up GitHub and deploying to AWS.

---

## Part 1: GitHub Setup & Upload

### Step 1: Check Current Git Status

First, let's check if you have Git installed and see your current configuration:

```bash
# Check Git version
git --version

# Check your Git configuration
git config --global user.name
git config --global user.email
```

If you need to set your Git identity:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 2: Check GitHub Connection in Cursor

**In Cursor IDE:**
1. Open Command Palette: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Git: Show Git Output" to see Git status
3. Or go to Source Control panel (left sidebar) - you'll see Git status there

**To check if GitHub is linked:**
- Look at the bottom-right corner of Cursor - it may show your Git status
- Or use terminal: `git remote -v` (after initializing repo)

### Step 3: Initialize Git Repository

```bash
# Navigate to your project directory
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Initialize Git repository
git init

# Check status
git status
```

### Step 4: Create GitHub Repository

**Option A: Using GitHub Website (Recommended for beginners)**

1. Go to [github.com](https://github.com) and sign in
2. Click the "+" icon in top-right → "New repository"
3. Repository name: `NewsVerify` (or your preferred name)
4. Description: "Fake News Detection System using AWS SageMaker and Elastic Beanstalk"
5. Choose **Public** or **Private**
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

**Option B: Using GitHub CLI (if installed)**

```bash
# Install GitHub CLI if not installed
# Mac: brew install gh
# Then authenticate: gh auth login

# Create repository
gh repo create NewsVerify --public --source=. --remote=origin --push
```

### Step 5: Add Files and Commit

```bash
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status

# Create initial commit
git commit -m "Initial commit"

# View commit history
git log --oneline
```

### Step 6: Connect to GitHub and Push

```bash
# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/NewsVerify.git

# Verify remote is added
git remote -v

# Push to GitHub (first time)
git branch -M main
git push -u origin main
```

**If you get authentication errors:**
- GitHub no longer accepts passwords for HTTPS
- Use a Personal Access Token instead:
  1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. Generate new token with `repo` permissions
  3. Use token as password when pushing

**Or use SSH (recommended):**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Then use SSH URL:
git remote set-url origin git@github.com:YOUR_USERNAME/NewsVerify.git
git push -u origin main
```

### Step 7: Verify Upload

1. Go to your GitHub repository page
2. You should see all your files
3. Check that `models/` and `processed_data/` are NOT uploaded (they're in .gitignore)

---

## Part 2: AWS Deployment - Complete Step-by-Step

### Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS Account created ([aws.amazon.com](https://aws.amazon.com))
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS CLI configured (`aws configure`)
- [ ] Python 3.8+ installed
- [ ] Basic understanding of AWS services

### Phase 1: AWS Account Setup

#### Step 1: Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the signup process
4. **Important**: Have a credit card ready (AWS Free Tier available)

#### Step 2: Install and Configure AWS CLI

**Install AWS CLI:**
```bash
# Mac
brew install awscli

# Or using pip
pip install awscli

# Verify installation
aws --version
```

**Configure AWS CLI:**
```bash
aws configure
```

You'll need:
- **AWS Access Key ID**: Get from IAM → Users → Your User → Security credentials → Create access key
- **AWS Secret Access Key**: Same place (shown only once - save it!)
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

**Verify configuration:**
```bash
aws sts get-caller-identity
```

### Phase 2: Prepare Your Data and Models

#### Step 3: Preprocess Data Locally

```bash
# Navigate to project directory
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Preprocess the dataset
python scripts/preprocess_data.py data.csv processed_data
```

This creates processed data files in `processed_data/` directory.

#### Step 4: Train Model Locally (Optional - for testing)

If you want to test locally first:
```bash
python scripts/train_local.py
```

This will create `models/model.pkl` and other model files.

### Phase 3: Set Up AWS S3

#### Step 5: Create S3 Bucket

```bash
# Create S3 bucket (bucket names must be globally unique)
aws s3 mb s3://newsverify-models-YOUR_UNIQUE_ID --region us-east-1

# Example: aws s3 mb s3://newsverify-models-2024 --region us-east-1

# List buckets to verify
aws s3 ls
```

**Note**: Replace `YOUR_UNIQUE_ID` with something unique (numbers, your name, etc.)

#### Step 6: Upload Processed Data to S3

```bash
# Upload processed data (for training)
aws s3 cp processed_data/ s3://newsverify-models-YOUR_UNIQUE_ID/training_data/ --recursive

aws s3 cp processed_data/ s3://newsverify-models-2026/training_data/ --recursive
# Verify upload
aws s3 ls s3://newsverify-models-YOUR_UNIQUE_ID/training_data/

aws s3 ls s3://newsverify-models-2026/training_data/
```

### Phase 4: Set Up IAM Roles

#### Step 7: Create SageMaker Execution Role

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Roles" → "Create role"
3. Select "AWS service" → "SageMaker"
4. Click "Next"
5. Attach policies:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess`
   - `CloudWatchFullAccess`
6. Click "Next"
7. Role name: `SageMakerExecutionRole`
8. Click "Create role"
9. **Copy the Role ARN** (looks like: `arn:aws:iam::123456789012:role/SageMakerExecutionRole`)
arn:aws:iam::587821825538:role/SageMakerExecutionRole

#### Step 8: Create EC2 Instance Profile (for EC2 Deployment)

1. In IAM Console → "Roles" → "Create role"
2. Select "AWS service" → "EC2"
3. Click "Next"
4. Attach policies:
   - `AmazonS3ReadOnlyAccess` (or create custom policy for your bucket)
   - `CloudWatchLogsFullAccess`
5. Click "Next"
6. Role name: `NewsVerify-EC2-Role`
7. Click "Create role"
8. **Note the Role ARN** for later 
arn:aws:iam::587821825538:role/NewsVerify-EC2-Role

### Phase 5: Train Model on SageMaker

#### Step 9: Upload Training Scripts to S3

```bash
# Create a directory for training code
mkdir -p training_code
cp scripts/train_sagemaker.py training_code/train.py

# Create a tar.gz file (SageMaker requirement)
tar -czf training_code.tar.gz training_code/

# Upload to S3
aws s3 cp training_code.tar.gz s3://newsverify-models-YOUR_UNIQUE_ID/code/training_code.tar.gz

aws s3 cp training_code.tar.gz s3://newsverify-models-2026/code/training_code.tar.gz
```

#### Step 10: Train Model on SageMaker

**Option A: Using Python Script**

```bash
python scripts/sagemaker_train.py \
    --bucket newsverify-models-2026 \
    --data-path processed_data \
    --instance-type ml.m5.xlarge \
    --role arn:aws:iam::587821825538:role/SageMakerExecutionRole
```

**Option B: Using AWS Console**

1. Go to [SageMaker Console](https://console.aws.amazon.com/sagemaker/)
2. Click "Training" → "Training jobs" → "Create training job"
3. Configure:
   - **Job name**: `newsverify-training-20260109`
   - **Algorithm**: Custom (use your training script)
   - **Input data**: `s3://newsverify-models-YOUR_UNIQUE_ID/training_data/`
   - **Output location**: `s3://newsverify-models-YOUR_UNIQUE_ID/models/`
   - **Instance type**: `ml.m5.xlarge`
   - **IAM role**: Select `SageMakerExecutionRole`
4. Click "Create training job"
5. Wait for training (15-30 minutes)
6. Monitor progress in the console

#### Step 11: Download Model from SageMaker

After training completes:

```bash
# Find the model artifact path from SageMaker console
# It will be: s3://newsverify-models-YOUR_UNIQUE_ID/models/training-job-name/output/model.tar.gz

# Download model
aws s3 cp s3://newsverify-models-YOUR_UNIQUE_ID/models/TRAINING_JOB_NAME/output/model.tar.gz ./model.tar.gz

aws s3 cp s3://sagemaker-us-east-1-587821825538/sagemaker-xgboost-2026-01-09-15-23-50-863/output/model.tar.gz


(venv) nikhiltamatta@Nikhils-MacBook-Air NewsVerify % aws s3 cp s3://sagemaker-us-east-1-587821825538/sagemaker-xgboost-2026-01-09-15-23-50-863/output/model.tar.gz .
download: s3://sagemaker-us-east-1-587821825538/sagemaker-xgboost-2026-01-09-15-23-50-863/output/model.tar.gz to ./model.tar.gz

# Extract
tar -xzf model.tar.gz

# Move model files to models directory
mkdir -p models
mv model.pkl models/
```

#### Step 12: Upload Model Files to S3

```bash
# Upload all model files to S3
aws s3 cp models/model.pkl s3://newsverify-models-YOUR_UNIQUE_ID/models/model.pkl
aws s3 cp processed_data/tfidf_vectorizer.pkl s3://newsverify-models-YOUR_UNIQUE_ID/models/tfidf_vectorizer.pkl
aws s3 cp processed_data/label_encoder.pkl s3://newsverify-models-YOUR_UNIQUE_ID/models/label_encoder.pkl
aws s3 cp processed_data/stat_feature_names.pkl s3://newsverify-models-YOUR_UNIQUE_ID/models/stat_feature_names.pkl


aws s3 cp models/model.pkl s3://newsverify-models-2026/models/model.pkl
aws s3 cp models/tfidf_vectorizer.pkl s3://newsverify-models-2026/models/tfidf_vectorizer.pkl
aws s3 cp models/label_encoder.pkl s3://newsverify-models-2026/models/label_encoder.pkl
aws s3 cp models/stat_feature_names.pkl s3://newsverify-models-2026/models/stat_feature_names.pkl

# Verify upload
aws s3 ls s3://newsverify-models-YOUR_UNIQUE_ID/models/

aws s3 ls s3://newsverify-models-2026/models/
```

### Phase 6: Deploy to EC2

See **[EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)** for complete step-by-step EC2 deployment instructions.

**Quick Summary:**

#### Step 13: Create EC2 Instance

1. Go to [EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click **Launch Instance**
3. Configure:
   - **AMI**: Amazon Linux 2023 or Ubuntu 22.04
   - **Instance type**: `t3.medium` or `t3.large`
   - **Key pair**: Create or select existing
   - **Security group**: Allow SSH (22) and HTTP (80)
4. Launch instance

#### Step 14: Create IAM Role for EC2

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Create role → AWS service → EC2
3. Attach policies:
   - `AmazonS3ReadOnlyAccess`
   - `CloudWatchLogsFullAccess`
4. Role name: `NewsVerify-EC2-Role`
5. Attach role to EC2 instance

#### Step 15: Set Up Application on EC2

1. SSH into instance
2. Install Python and dependencies
3. Upload application files
4. Configure Gunicorn service
5. Configure Nginx
6. Set environment variables

#### Step 16: Start Services

```bash
# On EC2 instance
sudo systemctl start newsverify
sudo systemctl start nginx
sudo systemctl enable newsverify
sudo systemctl enable nginx
```

#### Step 17: Test Application

```bash
# Get EC2 public IP
# Test health endpoint
curl http://<EC2_IP>/health

# Test prediction
curl -X POST http://<EC2_IP>/predict \
  -H "Content-Type: application/json" \
  -d '{"headline": "Test news headline"}'
```

For detailed instructions, see: [EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)

### Phase 7: Monitoring and Maintenance

#### Step 18: View Logs

```bash
# On EC2 instance
# View application logs
sudo journalctl -u newsverify -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

#### Step 19: Monitor with CloudWatch

1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Click "Metrics" → "All metrics"
3. Look for namespace `NewsVerify`:
   - `NewsVerify/Predictions`: Number of predictions
   - `NewsVerify/Confidence`: Confidence scores
   - `NewsVerify/PredictionErrors`: Error count
4. Also monitor EC2 metrics:
   - CPU utilization
   - Memory usage
   - Network traffic

#### Step 20: Set Up Alarms (Optional)

1. In CloudWatch → "Alarms" → "Create alarm"
2. Select metric: `NewsVerify/PredictionErrors` or EC2 CPU utilization
3. Set threshold (e.g., > 10 errors in 5 minutes, or CPU > 80%)
4. Configure SNS notification (optional)

---

## Part 3: Troubleshooting Common Issues

### Issue 1: Git Authentication Failed

**Problem**: `remote: Support for password authentication was removed`

**Solution**: Use Personal Access Token or SSH keys (see Part 1, Step 6)

### Issue 2: AWS CLI Not Configured

**Problem**: `Unable to locate credentials`

**Solution**:
```bash
aws configure
# Enter your Access Key ID and Secret Access Key
```

### Issue 3: S3 Bucket Name Already Exists

**Problem**: `BucketAlreadyExists`

**Solution**: Bucket names must be globally unique. Use a unique identifier:
```bash
aws s3 mb s3://newsverify-models-$(date +%s) --region us-east-1
```

### Issue 4: Model Not Loading on EC2

**Problem**: Application shows "Model not available"

**Solutions**:
1. Check S3 bucket permissions:
   ```bash
   aws s3 ls s3://newsverify-models-2026/models/
   ```
2. Verify environment variables in systemd service:
   ```bash
   # On EC2 instance
   sudo cat /etc/systemd/system/newsverify.service | grep Environment
   ```
3. Check IAM role attached to EC2 instance has S3 read permissions
4. View application logs:
   ```bash
   # On EC2 instance
   sudo journalctl -u newsverify -f
   ```
5. Verify IAM role is attached: EC2 Console → Instance → Security → IAM role

### Issue 5: Import Errors on EC2

**Problem**: `ModuleNotFoundError`

**Solutions**:
1. Check `requirements.txt` includes all dependencies
2. Verify Python version (3.8+)
3. Check application logs:
   ```bash
   # On EC2 instance
   sudo journalctl -u newsverify -f
   ```
4. Verify virtual environment is activated and dependencies installed
5. Reinstall dependencies if needed:
   ```bash
   # On EC2 instance
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Issue 6: High Memory Usage / Application Crashes

**Solutions**:
1. Increase instance size:
   ```bash
   eb config
   # Edit instance type to t3.medium or t3.large
   ```
2. Or via console: Configuration → Capacity → Instance types

---

## Part 4: Useful Commands Reference

### Git Commands
```bash
git status                    # Check status
git add .                     # Add all files
git commit -m "message"       # Commit changes
git push                      # Push to GitHub
git pull                      # Pull from GitHub
git log --oneline            # View commit history
```

### AWS CLI Commands
```bash
aws s3 ls                     # List S3 buckets
aws s3 cp file s3://bucket/   # Upload file
aws s3 sync dir/ s3://bucket/ # Sync directory
aws configure                 # Configure AWS CLI
aws sts get-caller-identity   # Check AWS identity
```

### EC2 Commands
```bash
# SSH into instance
ssh -i your-key.pem ec2-user@<EC2_IP>

# On EC2 instance:
sudo systemctl status newsverify    # Check app status
sudo systemctl restart newsverify   # Restart app
sudo journalctl -u newsverify -f   # View app logs
sudo systemctl status nginx        # Check Nginx status
sudo nginx -t                      # Test Nginx config
```

---

## Part 5: Cost Optimization Tips

1. **Stop SageMaker training instances** after training completes
2. **Stop EC2 instance** when not in use (saves costs)
3. **Use smaller EC2 instances** for development (t3.small)
4. **Delete unused S3 objects** periodically
5. **Use Reserved Instances** for production (save ~30-40%)
6. **Set up billing alerts** in AWS Console

**Estimated Monthly Costs:**
- S3 Storage: ~$0.50-2/month
- EC2 Instance (t3.medium): ~$30/month
- EC2 Instance (t3.large): ~$60/month
- CloudWatch: Free tier (10 custom metrics)
- **Total**: ~$30-60/month for development

---

## Next Steps After Deployment

1. **Custom Domain**: Point domain to EC2 public IP
2. **HTTPS**: Set up SSL certificate with Let's Encrypt
3. **Auto-scaling**: Use Auto Scaling Groups (if needed)
4. **CI/CD**: Set up automated deployment pipeline with GitHub Actions
5. **Monitoring Alarms**: Set up CloudWatch alarms for errors
6. **Backup Strategy**: Regular backups of model files
7. **Load Balancer**: Add Application Load Balancer (if needed)

---

## Getting Help

- **AWS Documentation**: [docs.aws.amazon.com](https://docs.aws.amazon.com)
- **Elastic Beanstalk Guide**: [docs.aws.amazon.com/elasticbeanstalk](https://docs.aws.amazon.com/elasticbeanstalk)
- **GitHub Help**: [help.github.com](https://help.github.com)
- **Check logs**: `eb logs` for deployment issues

---

**Good luck with your deployment! 🚀**
