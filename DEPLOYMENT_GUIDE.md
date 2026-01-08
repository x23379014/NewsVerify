# Deployment Guide - NewsVerify

This guide walks you through deploying the NewsVerify fake news detection system on AWS.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Python 3.8+** installed
4. **SageMaker Execution Role** created in IAM

## Step-by-Step Deployment

### Step 1: Create S3 Bucket

```bash
# Create S3 bucket for storing data and models
aws s3 mb s3://newsverify-models --region us-east-1

# Or use existing bucket, update bucket name in scripts
```

### Step 2: Preprocess Data Locally

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Preprocess the dataset
python scripts/preprocess_data.py data.csv processed_data
```

This creates:
- `processed_data/X_train.npz`, `X_val.npz`, `X_test.npz`
- `processed_data/y_train.npy`, `y_val.npy`, `y_test.npy`
- `processed_data/tfidf_vectorizer.pkl`
- `processed_data/label_encoder.pkl`
- `processed_data/stat_feature_names.pkl`

### Step 3: Upload Data to S3

```bash
# Upload processed data to S3
aws s3 cp processed_data/ s3://newsverify-models/training_data/ --recursive
```

### Step 4: Create SageMaker Execution Role

1. Go to IAM Console → Roles
2. Create role → AWS service → SageMaker
3. Attach policies:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess`
   - `CloudWatchFullAccess`
4. Note the Role ARN (e.g., `arn:aws:iam::123456789012:role/SageMakerExecutionRole`)

### Step 5: Train Model on SageMaker

#### Option A: Using the Training Script

```bash
python scripts/sagemaker_train.py \
    --bucket newsverify-models \
    --data-path processed_data \
    --instance-type ml.m5.xlarge \
    --role arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole
```

#### Option B: Manual Training via AWS Console

1. Go to SageMaker Console → Training → Training Jobs
2. Create training job
3. Configure:
   - **Algorithm**: XGBoost (built-in)
   - **Input data**: `s3://newsverify-models/training_data/`
   - **Output location**: `s3://newsverify-models/models/`
   - **Instance type**: `ml.m5.xlarge`
   - **Hyperparameters**: Use defaults or customize

4. Wait for training to complete (15-30 minutes)

### Step 6: Download Model from SageMaker

After training completes:

```bash
# Find the model artifact path from SageMaker console
# It will be something like: s3://newsverify-models/training-job-name/output/model.tar.gz

# Extract and upload model files
# The model.pkl should be inside the tar.gz file
# Extract it and upload to S3:

aws s3 cp models/model.pkl s3://newsverify-models/models/model.pkl
aws s3 cp processed_data/tfidf_vectorizer.pkl s3://newsverify-models/models/tfidf_vectorizer.pkl
aws s3 cp processed_data/label_encoder.pkl s3://newsverify-models/models/label_encoder.pkl
aws s3 cp processed_data/stat_feature_names.pkl s3://newsverify-models/models/stat_feature_names.pkl
```

### Step 7: Set Up Elastic Beanstalk

#### Install EB CLI

```bash
pip install awsebcli
```

#### Initialize Elastic Beanstalk

```bash
# Initialize EB in your project
eb init -p python-3.8 newsverify-app --region us-east-1

# This will prompt for:
# - AWS credentials (if not configured)
# - Region (choose same as S3 bucket)
# - Application name
```

#### Create Environment

```bash
# Create Elastic Beanstalk environment
eb create newsverify-env

# This will:
# - Create EC2 instance
# - Set up load balancer
# - Deploy your application
# - Take 5-10 minutes
```

#### Configure Environment Variables

```bash
# Set environment variables for S3 access
eb setenv S3_BUCKET=newsverify-models \
          MODEL_KEY=models/model.pkl \
          VECTORIZER_KEY=models/tfidf_vectorizer.pkl \
          LABEL_ENCODER_KEY=models/label_encoder.pkl \
          STAT_FEATURES_KEY=models/stat_feature_names.pkl \
          AWS_DEFAULT_REGION=us-east-1
```

#### Set Up IAM Instance Profile

The EC2 instance needs permissions to access S3 and CloudWatch:

1. Go to IAM → Roles
2. Create role → AWS service → EC2
3. Attach policies:
   - `AmazonS3ReadOnlyAccess` (or custom policy for your bucket)
   - `CloudWatchLogsFullAccess`
4. Go to Elastic Beanstalk Console → Your Environment → Configuration → Security
5. Attach the IAM instance profile to your environment

### Step 8: Deploy Application

```bash
# Deploy to Elastic Beanstalk
eb deploy

# This will:
# - Package your application
# - Upload to S3
# - Deploy to EC2 instances
# - Restart the application
```

### Step 9: Test Deployment

```bash
# Open the application in browser
eb open

# Or get the URL
eb status
```

### Step 10: Monitor with CloudWatch

1. Go to CloudWatch Console
2. View metrics under namespace `NewsVerify`:
   - Predictions count
   - Confidence scores
   - Error rates

3. View logs:
```bash
eb logs
```

## Troubleshooting

### Model Not Loading

**Issue**: Application shows "Model not available"

**Solutions**:
1. Check S3 bucket permissions
2. Verify model files are uploaded correctly:
   ```bash
   aws s3 ls s3://newsverify-models/models/
   ```
3. Check environment variables:
   ```bash
   eb printenv
   ```
4. Check IAM instance profile has S3 read permissions

### Import Errors

**Issue**: ModuleNotFoundError or import errors

**Solutions**:
1. Check `requirements.txt` includes all dependencies
2. Verify Python version (3.8+)
3. Check deployment logs:
   ```bash
   eb logs
   ```

### High Memory Usage

**Issue**: Application crashes or slow responses

**Solutions**:
1. Increase instance size in Elastic Beanstalk configuration
2. Use larger instance type (t3.medium or t3.large)
3. Optimize model loading (lazy loading is already implemented)

### CloudWatch Not Logging

**Issue**: No metrics in CloudWatch

**Solutions**:
1. Check IAM permissions for CloudWatch
2. Verify boto3 is installed
3. Check application logs for CloudWatch errors

## Cost Optimization

1. **Stop SageMaker training instances** after training completes
2. **Use smaller Elastic Beanstalk instances** for development (t3.small)
3. **Enable auto-scaling** only if needed
4. **Delete unused S3 objects** periodically
5. **Use Reserved Instances** for production

## Next Steps

1. **Custom Domain**: Configure custom domain in Elastic Beanstalk
2. **HTTPS**: Enable SSL certificate
3. **Auto-scaling**: Configure auto-scaling based on traffic
4. **Monitoring Alarms**: Set up CloudWatch alarms for errors
5. **CI/CD**: Set up automated deployment pipeline

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
```

## Support

For issues:
1. Check Elastic Beanstalk logs: `eb logs`
2. Check CloudWatch logs in AWS Console
3. Verify all environment variables are set
4. Check IAM permissions

