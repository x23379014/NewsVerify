# NewsVerify - Fake News Detection System

A cloud-based Machine Learning system for detecting fake news using AWS SageMaker, XGBoost, and EC2.

## Project Overview

This project implements a fake news detection system using:
- **ML Model**: XGBoost Classifier
- **Cloud Platform**: AWS
- **Services Used**:
  - AWS SageMaker (Model Training)
  - Amazon S3 (Data Storage)
  - Amazon EC2 (Web Application Deployment)
  - Amazon CloudWatch (Monitoring & Logging)

## Project Structure

```
NewsVerify/
├── app/                    # Flask web application
│   ├── __init__.py
│   ├── routes.py           # API routes
│   ├── static/             # CSS, JS files
│   │   ├── style.css
│   │   └── script.js
│   └── templates/          # HTML templates
│       └── index.html
├── scripts/                # Training and preprocessing scripts
│   ├── preprocess_data.py
│   ├── train_sagemaker.py
│   ├── sagemaker_train.py
│   └── download_model_from_sagemaker.py
├── notebooks/              # Jupyter notebooks for EDA
│   └── eda.ipynb
├── models/                 # Local model storage (gitignored)
├── processed_data/         # Processed datasets (gitignored)
├── data.csv               # Dataset
├── application.py         # Flask app entry point
├── requirements.txt       # Python dependencies
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- AWS Account with appropriate permissions
- AWS CLI configured
- SageMaker execution role

### 2. Local Setup

```bash
# Clone or navigate to project directory
cd NewsVerify

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab', quiet=True)"
```

### 3. Data Preprocessing

```bash
# Preprocess the dataset
python scripts/preprocess_data.py data.csv processed_data
```

This will:
- Clean and preprocess text
- Extract TF-IDF features
- Extract statistical features
- Split into train/validation/test sets
- Save processed data to `processed_data/` directory

### 4. Train Model on SageMaker

#### Option A: Using SageMaker Script

```bash
# Upload data to S3 and train
python scripts/sagemaker_train.py \
    --bucket newsverify-models-2026 \
    --data-path processed_data \
    --instance-type ml.m4.xlarge \
    --role <your-sagemaker-role-arn>
```

**Note:** Using `ml.m4.xlarge` instance type (Free Tier eligible alternative to `ml.m5.xlarge`)

#### Option B: Manual SageMaker Training

1. Upload processed data to S3:
```bash
aws s3 cp processed_data/ s3://newsverify-models-2026/training_data/ --recursive
```

2. Create SageMaker training job using the AWS Console or CLI

3. After training, download model artifacts:
```bash
python scripts/download_model_from_sagemaker.py \
    --bucket newsverify-models-2026 \
    --model-path s3://newsverify-models-2026/<training-job-name>/output/model.tar.gz
```

### 5. Upload Model to S3

After training, upload model files to S3 for EC2 deployment:

```bash
# Upload model and preprocessors
aws s3 cp models/model.pkl s3://newsverify-models-2026/models/model.pkl
aws s3 cp models/tfidf_vectorizer.pkl s3://newsverify-models-2026/models/tfidf_vectorizer.pkl
aws s3 cp models/label_encoder.pkl s3://newsverify-models-2026/models/label_encoder.pkl
aws s3 cp models/stat_feature_names.pkl s3://newsverify-models-2026/models/stat_feature_names.pkl
```

### 6. Deploy to EC2

**Quick Summary:**
1. Create EC2 instance (t3.medium recommended, or t3.large for higher performance)
2. Attach IAM role with S3 read permissions
3. Configure security group to allow HTTP (port 80) and SSH (port 22)
4. SSH into instance and set up environment:
   ```bash
   # Install Python, Nginx, and dependencies
   sudo dnf install python3.9 python3-pip nginx -y
   
   # Create virtual environment
   python3.9 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Download NLTK data
   python -c "import nltk; nltk.download('punkt_tab', quiet=True)"
   ```
5. Configure Gunicorn as systemd service
6. Configure Nginx as reverse proxy
7. Start services:
   ```bash
   sudo systemctl start newsverify
   sudo systemctl enable newsverify
   sudo systemctl start nginx
   sudo systemctl enable nginx
   ```

**Important Notes:**
- Ensure `/home/ec2-user/` has `755` permissions for Nginx to access static files
- Static files should be at `/home/ec2-user/newsverify/app/static/`
- Model files are automatically loaded from S3 on application startup

## Usage

### Web Interface

1. Navigate to your EC2 instance public IP (e.g., `http://your-ec2-ip`) or `http://localhost:5001` for local development
2. Enter a news headline (required)
3. Optionally enter article body and source URL
4. Click "Verify News" to get prediction

**Current Deployment:**
- The application is deployed on EC2 and accessible via public IP
- Static files (CSS/JS) are served by Nginx
- Model is loaded from S3 bucket: `newsverify-models-2026`

### API Endpoint

**Health Check:**
```bash
curl http://your-ec2-ip/health
```

**Prediction:**
```bash
curl -X POST http://your-ec2-ip/predict \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Your news headline here",
    "body": "Article body text (optional)",
    "url": "https://example.com (optional)"
  }'
```

Response:
```json
{
  "prediction": "FAKE" or "REAL",
  "confidence": 0.95,
  "probabilities": {
    "fake": 0.05,
    "real": 0.95
  }
}
```

## Model Details

### Features Used

1. **TF-IDF Features** (5000 features)
   - Unigrams and bigrams from headline + body
   - Max features: 5000
   - Min document frequency: 2

2. **Statistical Features** (13 features)
   - Headline: length, word count, uppercase ratio, punctuation count
   - Body: length, word count, sentence count, avg word length, punctuation, exclamation/question marks
   - URL: length, has_url flag
   - Combined: total length, headline-body ratio

### Model: XGBoost

- **Algorithm**: XGBoost Classifier
- **Hyperparameters**:
  - max_depth: 6
  - learning_rate (eta): 0.3
  - n_estimators: 100
  - subsample: 0.8
  - colsample_bytree: 0.8

## Monitoring

CloudWatch metrics are automatically logged:
- `NewsVerify/Predictions`: Number of predictions
- `NewsVerify/Confidence`: Prediction confidence scores
- `NewsVerify/PredictionErrors`: Error count

View logs:
```bash
# On EC2 instance
sudo journalctl -u newsverify -f
sudo tail -f /var/log/nginx/access.log
```

## Cost Estimation

- **SageMaker Training**: ~$2-5 per training job (ml.m4.xlarge)
- **S3 Storage**: ~$0.023/GB/month
- **EC2 Instance**: 
  - t3.medium: ~$30/month (recommended)
  - t3.large: ~$60/month (for higher performance)
- **CloudWatch**: Free tier includes 10 custom metrics

**Total Estimated Cost**: 
- Development/Production: ~$35-70/month (using t3.medium to t3.large)

## Troubleshooting

### Model not loading
- Check S3 bucket permissions
- Verify model files are uploaded correctly
- Check environment variables on EC2 instance
- Verify IAM role has S3 read permissions

### Import errors
- Ensure all dependencies are in `requirements.txt`
- Check Python version compatibility
- Verify virtual environment is activated

### Deployment issues
- Check Gunicorn service status: `sudo systemctl status newsverify`
- Check Nginx configuration: `sudo nginx -t`
- Review application logs: `sudo journalctl -u newsverify -f`
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### Static files (CSS/JS) not loading
- Ensure `/home/ec2-user/` has `755` permissions: `chmod 755 /home/ec2-user/`
- Verify static files are readable: `chmod 644 /home/ec2-user/newsverify/app/static/*`
- Check Nginx config has `/static` location block before `/` location
- Test static file access: `curl http://localhost/static/style.css`
- Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

## Development

### Local Testing

```bash
# Run Flask app locally
export S3_BUCKET=newsverify-models-2026
export MODEL_KEY=models/model.pkl
export VECTORIZER_KEY=models/tfidf_vectorizer.pkl
export LABEL_ENCODER_KEY=models/label_encoder.pkl
export STAT_FEATURES_KEY=models/stat_feature_names.pkl
export AWS_DEFAULT_REGION=us-east-1

python application.py
```

Visit `http://localhost:5001` (port changed to avoid macOS AirPlay conflict on port 5000)

### Recent Changes

- **Deployment**: Successfully deployed to EC2 with Nginx and Gunicorn
- **S3 Bucket**: Updated to `newsverify-models-2026`
- **Instance Type**: Using `ml.m4.xlarge` for SageMaker training (Free Tier alternative)
- **Port Configuration**: Local development uses port 5001, production uses port 5000 via Gunicorn
- **Static Files**: Configured Nginx to serve static files from `/app/static/`
- **NLTK Data**: Added `punkt_tab` resource download for NLTK compatibility

## License

This project is for educational purposes.

## Acknowledgments

- Dataset: [Kaggle Fake News Detection Dataset](https://www.kaggle.com/datasets/jruvika/fake-news-detection/data)
- AWS SageMaker Documentation
- XGBoost Library

