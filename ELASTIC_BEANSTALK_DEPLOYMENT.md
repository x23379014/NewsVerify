# Elastic Beanstalk Deployment Guide - NewsVerify

Complete step-by-step guide to deploy NewsVerify to AWS Elastic Beanstalk.

---

## Prerequisites

Before starting, ensure you have:

- [x] AWS Account with appropriate permissions
- [x] AWS CLI installed and configured (`aws configure`)
- [x] Elastic Beanstalk CLI installed
- [x] Model files uploaded to S3 (see previous steps)
- [x] IAM role created for EC2 instances

---

## Step 1: Install Elastic Beanstalk CLI

```bash
# Install EB CLI
pip install awsebcli

# Verify installation
eb --version
```

---

## Step 2: Initialize Elastic Beanstalk

```bash
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Initialize EB (will prompt for configuration)
eb init -p python-3.8 newsverify-app --region us-east-1
```

**What this does:**
- Creates `.elasticbeanstalk/` directory
- Sets up configuration files
- Prompts for:
  - AWS credentials (if not configured)
  - Region: `us-east-1`
  - Application name: `newsverify-app`

**Expected output:**
```
Select a platform branch.
1) Python 3.8 running on 64bit Amazon Linux 2
2) Python 3.9 running on 64bit Amazon Linux 2
3) Python 3.10 running on 64bit Amazon Linux 2
...
```

Choose option 1 (Python 3.8) or 2 (Python 3.9).

---

## Step 3: Create Elastic Beanstalk Environment

```bash
# Create environment (takes 5-10 minutes)
eb create newsverify-env
```

**What this does:**
- Creates EC2 instance
- Sets up load balancer
- Creates security groups
- Deploys your application
- Takes 5-10 minutes

**Monitor progress:**
```bash
# Check status
eb status

# View logs in real-time
eb logs --stream
```

---

## Step 4: Set Environment Variables

```bash
# Set environment variables for S3 access
eb setenv S3_BUCKET=newsverify-models-2026 \
          MODEL_KEY=models/model.pkl \
          VECTORIZER_KEY=models/tfidf_vectorizer.pkl \
          LABEL_ENCODER_KEY=models/label_encoder.pkl \
          STAT_FEATURES_KEY=models/stat_feature_names.pkl \
          AWS_DEFAULT_REGION=us-east-1
```

**Verify environment variables:**
```bash
eb printenv
```

---

## Step 5: Attach IAM Instance Profile

The EC2 instance needs permissions to access S3 and CloudWatch.

### Option A: Using AWS Console (Recommended)

1. Go to [Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk/)
2. Select your environment: `newsverify-env`
3. Click **Configuration** (left sidebar)
4. Click **Security** → **Edit**
5. Under **IAM instance profile**, select: `NewsVerify-EC2-Role`
   - If it doesn't exist, create it first (see Step 6)
6. Click **Apply**
7. Wait 2-3 minutes for update to complete

### Option B: Using EB CLI

```bash
# Edit configuration
eb config

# This opens an editor. Find the section:
#   aws:autoscaling:launchconfiguration:
#     IamInstanceProfile: aws-elasticbeanstalk-ec2-role

# Change to:
#   IamInstanceProfile: NewsVerify-EC2-Role

# Save and exit. Then:
eb config put
eb deploy
```

---

## Step 6: Create IAM Instance Profile (if not exists)

If `NewsVerify-EC2-Role` doesn't exist:

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Roles** → **Create role**
3. Select **AWS service** → **EC2**
4. Click **Next**
5. Attach policies:
   - `AmazonS3ReadOnlyAccess` (or custom policy for your bucket)
   - `CloudWatchLogsFullAccess`
6. Click **Next**
7. Role name: `NewsVerify-EC2-Role`
8. Click **Create role**

**Custom S3 Policy (if needed):**

If you want to restrict S3 access to only your bucket:

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

---

## Step 7: Deploy Application

```bash
# Deploy your application
eb deploy
```

**What this does:**
- Packages your application
- Uploads to S3
- Deploys to EC2 instances
- Restarts the application
- Takes 2-5 minutes

**Monitor deployment:**
```bash
# Watch logs
eb logs --stream

# Check status
eb status
```

---

## Step 8: Open and Test Application

```bash
# Open in browser
eb open

# Or get the URL
eb status
# Look for "CNAME" - that's your app URL
```

**Test the application:**
1. Visit the URL in your browser
2. Enter a test headline: "Scientists discover new planet"
3. Click "Verify News"
4. Check if prediction works

**Test API endpoint:**
```bash
# Get your app URL
APP_URL=$(eb status | grep CNAME | awk '{print $2}')

# Test health endpoint
curl http://$APP_URL/health

# Test prediction
curl -X POST http://$APP_URL/predict \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Breaking: Scientists discover new planet",
    "body": "Scientists have made an amazing discovery...",
    "url": "https://example.com"
  }'
```

---

## Step 9: View Logs

```bash
# View recent logs
eb logs

# View logs in real-time
eb logs --stream

# Download all logs
eb logs --all
```

---

## Troubleshooting

### Issue: Model Not Loading

**Symptoms:** Application shows "Model not available"

**Solutions:**
1. Check S3 bucket permissions:
   ```bash
   aws s3 ls s3://newsverify-models-2026/models/
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

5. SSH into instance and check:
   ```bash
   eb ssh
   # Then check /tmp/models/ directory
   ```

### Issue: Import Errors

**Symptoms:** ModuleNotFoundError

**Solutions:**
1. Check `requirements.txt` includes all dependencies
2. Verify Python version (3.8+)
3. Check deployment logs:
   ```bash
   eb logs
   ```

### Issue: High Memory Usage / Application Crashes

**Solutions:**
1. Increase instance size:
   ```bash
   eb config
   # Edit instance type to t3.medium or t3.large
   ```

2. Or via console: Configuration → Capacity → Instance types

### Issue: Timeout Errors

**Solutions:**
1. Increase timeout in Procfile (already set to 120 seconds)
2. Increase instance size
3. Check model loading time in logs

---

## Useful Commands

```bash
# View environment status
eb status

# View logs
eb logs

# SSH into instance
eb ssh

# Terminate environment (careful!)
eb terminate newsverify-env

# List all environments
eb list

# Open application
eb open

# View configuration
eb config

# View environment variables
eb printenv

# Set environment variable
eb setenv KEY=value

# Deploy
eb deploy

# Health check
eb health
```

---

## Update Application

After making code changes:

```bash
# Deploy updates
eb deploy

# Or commit and deploy
git add .
git commit -m "Update application"
eb deploy
```

---

## Cost Optimization

1. **Use smaller instances** for development (t3.small)
2. **Stop environment** when not in use:
   ```bash
   eb stop
   ```
3. **Resume environment**:
   ```bash
   eb start
   ```
4. **Terminate environment** when done (saves costs):
   ```bash
   eb terminate newsverify-env
   ```

**Estimated Costs:**
- t3.small: ~$15/month
- t3.medium: ~$30/month
- t3.large: ~$60/month

---

## Next Steps

1. **Custom Domain**: Configure custom domain in Elastic Beanstalk
2. **HTTPS**: Enable SSL certificate via AWS Certificate Manager
3. **Auto-scaling**: Configure auto-scaling based on traffic
4. **Monitoring Alarms**: Set up CloudWatch alarms for errors
5. **CI/CD**: Set up automated deployment pipeline

---

## Quick Reference

**Your Configuration:**
- Bucket: `newsverify-models-2026`
- Region: `us-east-1`
- IAM Role: `arn:aws:iam::587821825538:role/NewsVerify-EC2-Role`
- SageMaker Role: `arn:aws:iam::587821825538:role/SageMakerExecutionRole`

**Deployment Checklist:**
- [ ] EB CLI installed
- [ ] `eb init` completed
- [ ] `eb create` completed
- [ ] Environment variables set
- [ ] IAM instance profile attached
- [ ] Model files in S3
- [ ] Application deployed
- [ ] Application tested

---

**Good luck with your deployment! 🚀**
