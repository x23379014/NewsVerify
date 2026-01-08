# NewsVerify - Fake News Detection System

A cloud-based Machine Learning system for detecting fake news using AWS SageMaker, XGBoost, and Elastic Beanstalk.

## Project Overview

This project implements a fake news detection system using:
- **ML Model**: XGBoost Classifier
- **Cloud Platform**: AWS
- **Services Used**:
  - AWS SageMaker (Model Training)
  - Amazon S3 (Data Storage)
  - AWS Elastic Beanstalk (Web Application Deployment)
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
├── .ebextensions/         # Elastic Beanstalk configuration
├── .platform/             # Elastic Beanstalk platform hooks
├── data.csv               # Dataset
├── application.py         # Flask app entry point
├── requirements.txt       # Python dependencies
├── Procfile              # Elastic Beanstalk process file
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
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
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
    --bucket newsverify-models \
    --data-path processed_data \
    --instance-type ml.m5.xlarge \
    --role <your-sagemaker-role-arn>
```

#### Option B: Manual SageMaker Training

1. Upload processed data to S3:
```bash
aws s3 cp processed_data/ s3://newsverify-models/training_data/ --recursive
```

2. Create SageMaker training job using the AWS Console or CLI

3. After training, download model artifacts:
```bash
python scripts/download_model_from_sagemaker.py \
    --bucket newsverify-models \
    --model-path s3://newsverify-models/<training-job-name>/output/model.tar.gz
```

### 5. Upload Model to S3

After training, upload model files to S3 for Elastic Beanstalk:

```bash
# Upload model and preprocessors
aws s3 cp models/model.pkl s3://newsverify-models/models/model.pkl
aws s3 cp processed_data/tfidf_vectorizer.pkl s3://newsverify-models/models/tfidf_vectorizer.pkl
aws s3 cp processed_data/label_encoder.pkl s3://newsverify-models/models/label_encoder.pkl
aws s3 cp processed_data/stat_feature_names.pkl s3://newsverify-models/models/stat_feature_names.pkl
```

### 6. Deploy to Elastic Beanstalk

#### Install EB CLI

```bash
pip install awsebcli
```

#### Initialize Elastic Beanstalk

```bash
eb init -p python-3.8 newsverify-app --region us-east-1
```

#### Create Environment

```bash
eb create newsverify-env
```

#### Set Environment Variables

```bash
eb setenv S3_BUCKET=newsverify-models \
          MODEL_KEY=models/model.pkl \
          VECTORIZER_KEY=models/tfidf_vectorizer.pkl \
          LABEL_ENCODER_KEY=models/label_encoder.pkl \
          STAT_FEATURES_KEY=models/stat_feature_names.pkl
```

#### Deploy

```bash
eb deploy
```

#### Open Application

```bash
eb open
```

## Usage

### Web Interface

1. Navigate to the Elastic Beanstalk URL
2. Enter a news headline (required)
3. Optionally enter article body and source URL
4. Click "Verify News" to get prediction

### API Endpoint

```bash
curl -X POST https://your-app.elasticbeanstalk.com/predict \
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
eb logs
```

## Cost Estimation

- **SageMaker Training**: ~$2-5 per training job (ml.m5.xlarge)
- **S3 Storage**: ~$0.023/GB/month
- **Elastic Beanstalk**: ~$15-30/month (t3.small instance)
- **CloudWatch**: Free tier includes 10 custom metrics

**Total Estimated Cost**: ~$20-50 for development and testing

## Troubleshooting

### Model not loading
- Check S3 bucket permissions
- Verify model files are uploaded correctly
- Check environment variables in Elastic Beanstalk

### Import errors
- Ensure all dependencies are in `requirements.txt`
- Check Python version compatibility

### Deployment issues
- Check `.ebextensions` configuration
- Verify `Procfile` format
- Review Elastic Beanstalk logs: `eb logs`

## Development

### Local Testing

```bash
# Run Flask app locally
export S3_BUCKET=newsverify-models
export MODEL_KEY=models/model.pkl
export VECTORIZER_KEY=models/tfidf_vectorizer.pkl
export LABEL_ENCODER_KEY=models/label_encoder.pkl
export STAT_FEATURES_KEY=models/stat_feature_names.pkl

python application.py
```

Visit `http://localhost:5000`

## License

This project is for educational purposes.

## Acknowledgments

- Dataset: [Kaggle Fake News Detection Dataset](https://www.kaggle.com/datasets/jruvika/fake-news-detection/data)
- AWS SageMaker Documentation
- XGBoost Library

