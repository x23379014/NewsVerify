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

# Verify upload
aws s3 ls s3://newsverify-models-YOUR_UNIQUE_ID/training_data/
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

#### Step 8: Create EC2 Instance Profile (for Elastic Beanstalk)

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
```

#### Step 10: Train Model on SageMaker

**Option A: Using Python Script**

```bash
python scripts/sagemaker_train.py \
    --bucket newsverify-models-YOUR_UNIQUE_ID \
    --data-path processed_data \
    --instance-type ml.m5.xlarge \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole
```

**Option B: Using AWS Console**

1. Go to [SageMaker Console](https://console.aws.amazon.com/sagemaker/)
2. Click "Training" → "Training jobs" → "Create training job"
3. Configure:
   - **Job name**: `newsverify-training-YYYYMMDD`
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

# Verify upload
aws s3 ls s3://newsverify-models-YOUR_UNIQUE_ID/models/
```

### Phase 6: Deploy to Elastic Beanstalk

#### Step 13: Install Elastic Beanstalk CLI

```bash
pip install awsebcli

# Verify installation
eb --version
```

#### Step 14: Initialize Elastic Beanstalk

```bash
# Navigate to project directory
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Initialize EB (will prompt for configuration)
eb init -p python-3.8 newsverify-app --region us-east-1
```

This will:
- Ask for AWS credentials (if not configured)
- Create `.elasticbeanstalk/` directory
- Set up configuration files

#### Step 15: Create Elastic Beanstalk Environment

```bash
# Create environment (takes 5-10 minutes)
eb create newsverify-env

# This creates:
# - EC2 instance
# - Load balancer
# - Security groups
# - Auto-scaling group
```

**Monitor progress:**
```bash
eb status
eb health
```

#### Step 16: Configure Environment Variables

```bash
# Set environment variables (replace YOUR_UNIQUE_ID with your bucket name)
eb setenv S3_BUCKET=newsverify-models-YOUR_UNIQUE_ID \
          MODEL_KEY=models/model.pkl \
          VECTORIZER_KEY=models/tfidf_vectorizer.pkl \
          LABEL_ENCODER_KEY=models/label_encoder.pkl \
          STAT_FEATURES_KEY=models/stat_feature_names.pkl \
          AWS_DEFAULT_REGION=us-east-1
```

#### Step 17: Attach IAM Instance Profile

1. Go to [Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk/)
2. Select your environment: `newsverify-env`
3. Click "Configuration" → "Security"
4. Under "IAM instance profile", select `NewsVerify-EC2-Role`
5. Click "Apply"
6. Wait for environment update (2-3 minutes)

#### Step 18: Deploy Application

```bash
# Deploy your application
eb deploy

# This will:
# - Package your application
# - Upload to S3
# - Deploy to EC2 instances
# - Restart the application
```

#### Step 19: Open and Test Application

```bash
# Open in browser
eb open

# Or get the URL
eb status
```

**Test the application:**
1. Visit the URL in your browser
2. Enter a test headline: "Breaking: Scientists discover new planet"
3. Click "Verify News"
4. Check if prediction works

**Test API endpoint:**
```bash
# Get your app URL
APP_URL=$(eb status | grep CNAME | awk '{print $2}')

# Test prediction
curl -X POST http://$APP_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"headline": "Test news headline"}'
```

### Phase 7: Monitoring and Maintenance

#### Step 20: View Logs

```bash
# View recent logs
eb logs

# View logs in real-time
eb logs --stream

# View specific log files
eb logs --all
```

#### Step 21: Monitor with CloudWatch

1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
2. Click "Metrics" → "All metrics"
3. Look for namespace `NewsVerify`:
   - `NewsVerify/Predictions`: Number of predictions
   - `NewsVerify/Confidence`: Confidence scores
   - `NewsVerify/PredictionErrors`: Error count

#### Step 22: Set Up Alarms (Optional)

1. In CloudWatch → "Alarms" → "Create alarm"
2. Select metric: `NewsVerify/PredictionErrors`
3. Set threshold (e.g., > 10 errors in 5 minutes)
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

### Issue 4: Model Not Loading in Elastic Beanstalk

**Problem**: Application shows "Model not available"

**Solutions**:
1. Check S3 bucket permissions:
   ```bash
   aws s3 ls s3://newsverify-models-YOUR_UNIQUE_ID/models/
   ```
2. Verify environment variables:
   ```bash
   eb printenv
   ```
3. Check IAM instance profile has S3 read permissions
4. View application logs:
   ```bash
   eb logs
   ```

### Issue 5: Import Errors in Elastic Beanstalk

**Problem**: `ModuleNotFoundError`

**Solutions**:
1. Check `requirements.txt` includes all dependencies
2. Verify Python version (3.8+)
3. Check deployment logs:
   ```bash
   eb logs
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

### Elastic Beanstalk Commands
```bash
eb init                      # Initialize EB
eb create env-name           # Create environment
eb deploy                    # Deploy application
eb status                    # Check status
eb logs                      # View logs
eb open                      # Open in browser
eb terminate env-name        # Delete environment
eb config                    # Edit configuration
eb printenv                  # View environment variables
```

---

## Part 5: Cost Optimization Tips

1. **Stop SageMaker training instances** after training completes
2. **Use smaller Elastic Beanstalk instances** for development (t3.small)
3. **Enable auto-scaling** only if needed
4. **Delete unused S3 objects** periodically
5. **Use Reserved Instances** for production
6. **Set up billing alerts** in AWS Console

**Estimated Monthly Costs:**
- S3 Storage: ~$0.50-2/month
- Elastic Beanstalk (t3.small): ~$15-20/month
- CloudWatch: Free tier (10 custom metrics)
- **Total**: ~$20-25/month for development

---

## Next Steps After Deployment

1. **Custom Domain**: Configure custom domain in Elastic Beanstalk
2. **HTTPS**: Enable SSL certificate via AWS Certificate Manager
3. **Auto-scaling**: Configure auto-scaling based on traffic
4. **CI/CD**: Set up automated deployment pipeline with GitHub Actions
5. **Monitoring Alarms**: Set up CloudWatch alarms for errors
6. **Backup Strategy**: Regular backups of model files

---

## Getting Help

- **AWS Documentation**: [docs.aws.amazon.com](https://docs.aws.amazon.com)
- **Elastic Beanstalk Guide**: [docs.aws.amazon.com/elasticbeanstalk](https://docs.aws.amazon.com/elasticbeanstalk)
- **GitHub Help**: [help.github.com](https://help.github.com)
- **Check logs**: `eb logs` for deployment issues

---

**Good luck with your deployment! 🚀**
