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
aws s3 cp models/model.pkl s3://newsverify-models/models/model.pkl
aws s3 cp processed_data/tfidf_vectorizer.pkl s3://newsverify-models/models/tfidf_vectorizer.pkl
aws s3 cp processed_data/label_encoder.pkl s3://newsverify-models/models/label_encoder.pkl
aws s3 cp processed_data/stat_feature_names.pkl s3://newsverify-models/models/stat_feature_names.pkl
```

### 2. Create S3 Bucket (if not exists)
```bash
aws s3 mb s3://newsverify-models --region us-east-1
```

### 3. Set Up IAM Permissions
The EC2 instance needs an IAM role with:
- **S3 Read Access** to your bucket
- **CloudWatch Logs Write Access**

Create IAM role and attach to Elastic Beanstalk environment.

### 4. Configure Environment Variables
Set these in Elastic Beanstalk:
```bash
eb setenv S3_BUCKET=newsverify-models \
          MODEL_KEY=models/model.pkl \
          VECTORIZER_KEY=models/tfidf_vectorizer.pkl \
          LABEL_ENCODER_KEY=models/label_encoder.pkl \
          STAT_FEATURES_KEY=models/stat_feature_names.pkl \
          AWS_DEFAULT_REGION=us-east-1
```

## Files Ready for Deployment

### ✅ Configuration Files
- `.ebextensions/python.config` - Python/WSGI configuration
- `.ebextensions/01_packages.config` - System packages
- `.ebextensions/02_environment.config` - Environment variables
- `.platform/hooks/postdeploy/01_install_dependencies.sh` - Post-deploy script
- `Procfile` - Process configuration

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

## Deployment Steps

1. **Initialize EB** (if not done):
   ```bash
   eb init -p python-3.8 newsverify-app --region us-east-1
   ```

2. **Create Environment**:
   ```bash
   eb create newsverify-env
   ```

3. **Set Environment Variables**:
   ```bash
   eb setenv S3_BUCKET=newsverify-models \
             MODEL_KEY=models/model.pkl \
             VECTORIZER_KEY=models/tfidf_vectorizer.pkl \
             LABEL_ENCODER_KEY=models/label_encoder.pkl \
             STAT_FEATURES_KEY=models/stat_feature_names.pkl \
             AWS_DEFAULT_REGION=us-east-1
   ```

4. **Deploy**:
   ```bash
   eb deploy
   ```

5. **Check Logs**:
   ```bash
   eb logs
   ```

## Post-Deployment Verification

1. **Health Check**:
   ```bash
   curl https://your-app.elasticbeanstalk.com/health
   ```

2. **Test Prediction**:
   ```bash
   curl -X POST https://your-app.elasticbeanstalk.com/predict \
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
- Check environment variables are set
- Verify model files exist in S3

### Issue: Import errors
**Solution**:
- Check `requirements.txt` includes all dependencies
- Verify Python version (3.8+)

### Issue: Timeout errors
**Solution**:
- Increase instance size
- Check model loading time
- Review CloudWatch logs

## Notes

- The application will try to load models from local directory first (for development)
- If local models not found, it will download from S3
- CloudWatch logging is optional (gracefully handles if not available)
- All paths are relative or use environment variables

