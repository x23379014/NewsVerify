# AWS Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Review
- [x] AWS region configuration added
- [x] Environment variables properly configured
- [x] No hardcoded local paths (except /tmp which is fine)
- [x] Error handling for AWS services
- [x] JSON serialization fixed (numpy types handled)

### Required Changes Made
1. **AWS Region Configuration**: Added region support to boto3 clients
2. **Environment Variables**: All configurable via environment variables
3. **Error Handling**: Graceful fallback for local development

## Pre-Deployment Steps

### 1. Upload Model Files to S3
Before deploying, ensure your model files are in S3:

```bash
# Upload model files to S3
aws s3 cp models/model.pkl s3://newsverify-models-2026/models/model.pkl
aws s3 cp models/tfidf_vectorizer.pkl s3://newsverify-models-2026/models/tfidf_vectorizer.pkl
aws s3 cp models/label_encoder.pkl s3://newsverify-models-2026/models/label_encoder.pkl
aws s3 cp models/stat_feature_names.pkl s3://newsverify-models-2026/models/stat_feature_names.pkl
```

### 2. Create S3 Bucket (if not exists)
```bash
aws s3 mb s3://newsverify-models-2026 --region us-east-1
```

### 3. Set Up IAM Permissions
The EC2 instance needs an IAM role with:
- **S3 Read Access** to your bucket
- **CloudWatch Logs Write Access**

Create IAM role and attach to EC2 instance.

### 4. Configure Environment Variables
Set these on EC2 instance (in systemd service or .env file):
```bash
S3_BUCKET=newsverify-models-2026
MODEL_KEY=models/model.pkl
VECTORIZER_KEY=models/tfidf_vectorizer.pkl
LABEL_ENCODER_KEY=models/label_encoder.pkl
STAT_FEATURES_KEY=models/stat_feature_names.pkl
AWS_DEFAULT_REGION=us-east-1
```

## Files Ready for Deployment

### ✅ Configuration Files
- `ec2-setup.sh` - EC2 setup script
- `EC2_DEPLOYMENT_GUIDE.md` - Deployment guide
- Systemd service file (created on EC2)
- Nginx configuration (created on EC2)

### ✅ Application Files
- `application.py` - Flask app entry point
- `app/` - Application code
- `requirements.txt` - Python dependencies

### ⚠️ Files NOT to Deploy
- `data.csv` - Too large, not needed
- `processed_data/` - Not needed (data in S3)
- `models/` - Not needed (models in S3)
- `notebooks/` - For development only
- `.git/` - Version control
- `venv/` - Virtual environment (recreate on EC2)

## Deployment Steps

See **[EC2_DEPLOYMENT_GUIDE.md](EC2_DEPLOYMENT_GUIDE.md)** for complete deployment steps.

**Quick Summary:**

1. **Create EC2 Instance**:
   - EC2 Console → Launch Instance
   - Choose Amazon Linux or Ubuntu
   - Instance type: t3.medium or t3.large

2. **Create IAM Role**:
   - IAM → Roles → Create role → EC2
   - Attach S3 and CloudWatch policies
   - Attach to EC2 instance

3. **Set Up Application**:
   - SSH into instance
   - Run setup script or follow manual steps
   - Upload application files
   - Configure Gunicorn and Nginx

4. **Start Services**:
   ```bash
   sudo systemctl start newsverify
   sudo systemctl start nginx
   ```

5. **Check Logs**:
   ```bash
   sudo journalctl -u newsverify -f
   ```

## Post-Deployment Verification

1. **Health Check**:
   ```bash
   curl http://<EC2_IP>/health
   ```

2. **Test Prediction**:
   ```bash
   curl -X POST http://<EC2_IP>/predict \
     -H "Content-Type: application/json" \
     -d '{"headline": "Test news headline"}'
   ```

3. **Check CloudWatch Logs**:
   - View application logs in CloudWatch
   - Check for any errors

## Common Issues & Solutions

### Issue: Model not loading
**Solution**: 
- Verify S3 bucket permissions
- Check environment variables are set in systemd service
- Verify model files exist in S3
- Check IAM role attached to EC2 instance
- View application logs: `sudo journalctl -u newsverify -f`

### Issue: Import errors
**Solution**:
- Check `requirements.txt` includes all dependencies
- Verify Python version (3.8+)

### Issue: Timeout errors
**Solution**:
- Increase EC2 instance size
- Check model loading time
- Review application logs: `sudo journalctl -u newsverify -f`
- Increase Gunicorn timeout in systemd service

## Notes

- The application will try to load models from local directory first (for development)
- If local models not found, it will download from S3
- CloudWatch logging is optional (gracefully handles if not available)
- All paths are relative or use environment variables
- EC2 deployment uses Gunicorn + Nginx (not Elastic Beanstalk)
- See EC2_DEPLOYMENT_GUIDE.md for complete deployment instructions

