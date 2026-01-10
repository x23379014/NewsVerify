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
aws s3 mb s3://newsverify-models-2026 --region us-east-1

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
aws s3 cp processed_data/ s3://newsverify-models-2026/training_data/ --recursive
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
    --bucket newsverify-models-2026 \
    --data-path processed_data \
    --instance-type ml.m4.xlarge \
    --role arn:aws:iam::587821825538:role/SageMakerExecutionRole
```

#### Option B: Manual Training via AWS Console

1. Go to SageMaker Console → Training → Training Jobs
2. Create training job
3. Configure:
   - **Algorithm**: XGBoost (built-in)
   - **Input data**: `s3://newsverify-models-2026/training_data/`
   - **Output location**: `s3://newsverify-models-2026/models/`
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

aws s3 cp models/model.pkl s3://newsverify-models-2026/models/model.pkl
aws s3 cp models/tfidf_vectorizer.pkl s3://newsverify-models-2026/models/tfidf_vectorizer.pkl
aws s3 cp models/label_encoder.pkl s3://newsverify-models-2026/models/label_encoder.pkl
aws s3 cp models/stat_feature_names.pkl s3://newsverify-models-2026/models/stat_feature_names.pkl
```

### Step 7: Deploy to EC2

See **[EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)** for complete step-by-step EC2 deployment instructions.

**Quick Summary:**

1. **Create EC2 Instance**
   - Go to EC2 Console → Launch Instance
   - Choose: Amazon Linux 2023 or Ubuntu 22.04
   - Instance type: `t3.medium` or `t3.large`
   - Security group: Allow SSH (22) and HTTP (80)

2. **Create IAM Role for EC2**
   - IAM → Roles → Create role → EC2
   - Attach policies: `AmazonS3ReadOnlyAccess`, `CloudWatchLogsFullAccess`
   - Role name: `NewsVerify-EC2-Role`
   - Attach role to EC2 instance

3. **Set Up Application on EC2**
   - SSH into instance
   - Install Python, dependencies
   - Upload application files
   - Configure Gunicorn and Nginx
   - Set environment variables

4. **Start Services**
   - Start Gunicorn service
   - Start Nginx
   - Test application

For detailed instructions, see: [EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)

### Step 8: Monitor with CloudWatch

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
   aws s3 ls s3://newsverify-models-2026/models/
   ```
3. Check environment variables on EC2:
   ```bash
   # On EC2 instance
   cat /etc/systemd/system/newsverify.service | grep Environment
   ```
4. Check IAM role attached to EC2 instance has S3 read permissions
5. Verify IAM role is attached: EC2 Console → Instance → Security → IAM role

### Import Errors

**Issue**: ModuleNotFoundError or import errors

**Solutions**:
1. Check `requirements.txt` includes all dependencies
2. Verify Python version (3.8+)
3. Check application logs on EC2:
   ```bash
   # On EC2 instance
   sudo journalctl -u newsverify -f
   ```
4. Verify virtual environment is activated and dependencies installed

### High Memory Usage

**Issue**: Application crashes or slow responses

**Solutions**:
1. Increase EC2 instance size (t3.medium → t3.large)
2. Optimize Gunicorn workers (reduce workers if memory constrained)
3. Optimize model loading (lazy loading is already implemented)
4. Monitor with CloudWatch

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

1. **Custom Domain**: Point domain to EC2 public IP
2. **HTTPS**: Set up SSL certificate with Let's Encrypt
3. **Auto-scaling**: Use Auto Scaling Groups (if needed)
4. **Monitoring Alarms**: Set up CloudWatch alarms for errors
5. **CI/CD**: Set up automated deployment pipeline
6. **Load Balancer**: Add Application Load Balancer (if needed)

## Useful Commands

**On EC2 Instance:**

```bash
# View application logs
sudo journalctl -u newsverify -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart application
sudo systemctl restart newsverify

# Restart Nginx
sudo systemctl restart nginx

# Check service status
sudo systemctl status newsverify
sudo systemctl status nginx

# Test Nginx configuration
sudo nginx -t
```

**From Local Machine:**

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@<EC2_IP>

# Test application
curl http://<EC2_IP>/health
curl -X POST http://<EC2_IP>/predict -H "Content-Type: application/json" -d '{"headline":"test"}'
```

## Support

For issues:
1. Check Elastic Beanstalk logs: `eb logs`
2. Check CloudWatch logs in AWS Console
3. Verify all environment variables are set
4. Check IAM permissions

