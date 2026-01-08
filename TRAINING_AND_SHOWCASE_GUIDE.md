# Training and Showcase Guide - NewsVerify

This guide provides step-by-step commands for training the model and instructions for showcasing the project.

---

## Part 1: Training the Model

### Option A: Local Training (Quick Testing)

#### Step 1: Preprocess the Dataset

```bash
# Navigate to project directory
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Activate virtual environment (if using one)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Download NLTK data (first time only)
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Preprocess the dataset
python3 scripts/preprocess_data.py data.csv processed_data
```

**Expected Output:**
```
Loading data...
Dataset shape: (4009, 4)
Label distribution:
Label
0    2137
1    1872
Cleaning text...
Extracting statistical features...
Creating TF-IDF features...
Splitting data...
Saving processed data...

Preprocessing complete!
Train set: 2565 samples
Validation set: 642 samples
Test set: 802 samples
Total features: 5015
```

#### Step 2: Train Model Locally

```bash
# Train XGBoost model locally
python3 scripts/train_local.py \
    --data-dir processed_data \
    --model-dir models \
    --n-estimators 100 \
    --max-depth 6 \
    --eta 0.3
```

**Expected Output:**
```
Loading data...
Training set shape: (2565, 5015)
Validation set shape: (642, 5015)
Test set shape: (802, 5015)

Training XGBoost model...
[Training progress...]

Train Set Metrics:
Accuracy: 1.0000
Precision: 1.0000
Recall: 1.0000
F1-Score: 1.0000

Validation Set Metrics:
Accuracy: 0.9829
Precision: 0.9829
Recall: 0.9829
F1-Score: 0.9829

Test Set Metrics:
Accuracy: 0.9850
Precision: 0.9850
Recall: 0.9850
F1-Score: 0.9850

Model saved to models/model.pkl
✅ Training complete! Model ready for deployment.
```

#### Step 3: Verify Model Files

```bash
# Check that all model files are created
ls -lh models/

# Expected files:
# - model.pkl
# - tfidf_vectorizer.pkl
# - label_encoder.pkl
# - stat_feature_names.pkl
# - metrics.json
```

---

### Option B: AWS SageMaker Training (Production)

#### Step 1: Set Up AWS Credentials

```bash
# Configure AWS CLI (if not already done)
aws configure

# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

#### Step 2: Create S3 Bucket

```bash
# Create S3 bucket for storing data and models
aws s3 mb s3://newsverify-models --region us-east-1

# Verify bucket creation
aws s3 ls | grep newsverify-models
```

#### Step 3: Upload Preprocessed Data to S3

```bash
# Upload processed data to S3
aws s3 cp processed_data/ s3://newsverify-models/training_data/ --recursive

# Verify upload
aws s3 ls s3://newsverify-models/training_data/ --recursive
```

#### Step 4: Create SageMaker Execution Role

1. Go to AWS IAM Console: https://console.aws.amazon.com/iam/
2. Click "Roles" → "Create role"
3. Select "AWS service" → "SageMaker"
4. Attach policies:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess`
   - `CloudWatchFullAccess`
5. Name the role: `SageMakerExecutionRole`
6. Copy the Role ARN (e.g., `arn:aws:iam::123456789012:role/SageMakerExecutionRole`)

#### Step 5: Train Model on SageMaker

```bash
# Train model using SageMaker
python3 scripts/sagemaker_train.py \
    --bucket newsverify-models \
    --data-path processed_data \
    --instance-type ml.m5.xlarge \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerExecutionRole
```

**Note:** Replace `YOUR_ACCOUNT_ID` with your AWS account ID.

#### Step 6: Monitor Training Job

```bash
# Check training job status in AWS Console
# Or use AWS CLI:
aws sagemaker list-training-jobs --max-results 5

# View training logs
# Go to SageMaker Console → Training Jobs → Your Job → View Logs
```

#### Step 7: Download Model from SageMaker

After training completes (15-30 minutes):

```bash
# Find the model artifact path from SageMaker console
# It will be something like: s3://newsverify-models/training-job-name/output/model.tar.gz

# Download model artifacts
aws s3 cp s3://newsverify-models/YOUR-TRAINING-JOB/output/model.tar.gz ./model.tar.gz

# Extract model
tar -xzf model.tar.gz

# Copy model files to models directory
cp model.pkl models/
```

#### Step 8: Upload Model Files to S3 (for Elastic Beanstalk)

```bash
# Upload all model files to S3
aws s3 cp models/model.pkl s3://newsverify-models/models/model.pkl
aws s3 cp processed_data/tfidf_vectorizer.pkl s3://newsverify-models/models/tfidf_vectorizer.pkl
aws s3 cp processed_data/label_encoder.pkl s3://newsverify-models/models/label_encoder.pkl
aws s3 cp processed_data/stat_feature_names.pkl s3://newsverify-models/models/stat_feature_names.pkl

# Verify uploads
aws s3 ls s3://newsverify-models/models/
```

---

## Part 2: Running the Application Locally

### Start the Flask Application

```bash
# Navigate to project directory
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Start Flask app
python3 application.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
```

### Access the Application

Open your browser and navigate to:
- **http://localhost:5000**
- **http://127.0.0.1:5000**

### Test the API

```bash
# Health check
curl http://localhost:5000/health

# Test prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Scientists discover new planet in nearby star system",
    "body": "Astronomers have identified a new exoplanet that could potentially support life."
  }'
```

---

## Part 3: Showcasing the Project

### Demo Preparation Checklist

#### 1. Pre-Demo Setup

```bash
# Ensure model is trained
ls models/model.pkl

# Start the application
python3 application.py

# Test with sample inputs
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"headline": "Test headline"}'
```

#### 2. Prepare Demo Examples

Create a file `demo_examples.txt` with test cases:

```
REAL NEWS EXAMPLES:
1. "Scientists discover new planet in nearby star system"
2. "Global economy shows signs of recovery in Q3"
3. "New study reveals benefits of exercise on mental health"

FAKE NEWS EXAMPLES:
1. "BREAKING: Government hiding aliens in secret facility!"
2. "Miracle cure discovered - doctors don't want you to know!"
3. "Shocking truth: Celebrities are actually robots!"
```

#### 3. Screenshot Key Features

Take screenshots of:
- Homepage/UI
- Prediction results (both fake and real)
- Confidence scores
- AWS Console (S3, CloudWatch) - if deployed

---

### Demo Script (4-5 Minutes)

#### Introduction (30 seconds)

**What to say:**
"Good [morning/afternoon], Professor. I'm presenting **NewsVerify**, a fake news detection system using machine learning. The project uses XGBoost classifier trained on AWS SageMaker and deployed on Elastic Beanstalk."

#### System Architecture (1 minute)

**What to show/say:**
- "The system follows this architecture:
  1. Dataset preprocessing with TF-IDF and statistical features
  2. Model training on AWS SageMaker using XGBoost
  3. Model storage in S3
  4. Web application deployed on Elastic Beanstalk
  5. Real-time predictions with confidence scores"

**Visual:** Show architecture diagram or describe flow

#### Live Demo (2-3 minutes)

**Step 1: Open Application**
```bash
# Open browser to http://localhost:5000
# Or if deployed: https://your-app.elasticbeanstalk.com
```

**Step 2: Demo Real News**
- Enter: "Scientists discover new planet in nearby star system"
- Click "Verify News"
- Show result: "REAL NEWS - 87% confidence"
- Explain: "The model correctly identifies this as real news with high confidence"

**Step 3: Demo Fake News**
- Enter: "BREAKING: Government hiding aliens in secret facility!"
- Click "Verify News"
- Show result: "FAKE NEWS - 92% confidence"
- Explain: "The model detects suspicious patterns and flags this as fake"

**Step 4: Show Technical Details**
- Point out confidence scores
- Show probability breakdown (Fake vs Real percentages)
- Mention response time

#### Technical Highlights (1 minute)

**What to mention:**
- "The model achieved **98.5% accuracy** on the test set"
- "Uses **5,015 features**: TF-IDF vectors (5,000) + statistical features (15)"
- "Trained on **2,565 samples**, validated on **642**, tested on **802**"
- "Deployed on **AWS** for scalability and reliability"
- "Uses **XGBoost** for fast, accurate predictions"

#### Conclusion (30 seconds)

**What to say:**
"This system demonstrates end-to-end ML deployment on AWS, from data preprocessing to production deployment. The model performs well with high accuracy, and the system is scalable and production-ready. Thank you. I'm happy to answer any questions."

---

### Command Reference for Demo

#### Quick Start Commands

```bash
# 1. Start the application
cd /Users/nikhiltamatta/Desktop/NewsVerify
python3 application.py

# 2. In another terminal, test the API
curl http://localhost:5000/health

# 3. Test prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"headline": "Your test headline here"}'
```

#### Show Model Metrics

```bash
# Display model performance metrics
cat models/metrics.json | python3 -m json.tool
```

#### Check Model Files

```bash
# Verify all model files exist
ls -lh models/
echo "Model size:"
du -sh models/
```

---

### Potential Questions & Answers

#### Q: Why did you choose XGBoost?

**Answer:**
"I chose XGBoost because:
- It provides excellent performance (98.5% accuracy)
- Fast training and inference
- Works well with engineered features (TF-IDF + statistics)
- Cost-effective on AWS
- Interpretable results with feature importance"

#### Q: How does the model work?

**Answer:**
"The model processes text through:
1. **Text cleaning**: Remove URLs, special characters, stopwords
2. **TF-IDF vectorization**: Convert text to 5,000 numerical features
3. **Statistical features**: Extract 15 features (text length, punctuation, etc.)
4. **XGBoost classification**: Predict fake (0) or real (1) with confidence scores"

#### Q: What about ethical implications?

**Answer:**
"Key ethical considerations:
- **Bias**: Model may reflect biases in training data
- **Privacy**: User input data handling
- **Misuse**: Could be used to suppress legitimate news
- **Transparency**: Need to explain predictions
- **Accountability**: Human oversight required for critical decisions"

#### Q: Why AWS?

**Answer:**
"AWS provides:
- **Scalability**: Handle varying traffic loads
- **Managed services**: SageMaker, Elastic Beanstalk reduce operational overhead
- **Cost-effective**: Pay only for what you use
- **Industry standard**: Widely used in production ML systems
- **Integration**: Easy integration between services (S3, CloudWatch, etc.)"

#### Q: What's the model performance?

**Answer:**
"Performance metrics:
- **Accuracy**: 98.5%
- **Precision**: 98.5%
- **Recall**: 98.5%
- **F1-Score**: 98.5%
- **Test Set**: 802 samples
- **Training Time**: ~5 minutes locally, ~20 minutes on SageMaker"

---

### Demo Tips

1. **Practice First**: Run through the demo 2-3 times before presentation
2. **Have Backup**: Take screenshots/video in case of technical issues
3. **Keep It Simple**: Focus on what works, don't overcomplicate
4. **Be Confident**: You built a working system - show it proudly
5. **Prepare Examples**: Have 5-6 test headlines ready
6. **Show Enthusiasm**: Demonstrate your interest in the project

---

### Quick Demo Commands Cheat Sheet

```bash
# Start app
python3 application.py

# Health check
curl http://localhost:5000/health

# Test prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"headline": "Test headline"}'

# View metrics
cat models/metrics.json

# Check model files
ls -lh models/
```

---

### Video Recording (Optional)

If you want to record a backup video:

```bash
# On Mac: Use QuickTime or Screen Recording
# Record: 
# 1. Opening the app
# 2. Testing 2-3 examples
# 3. Showing results
# Keep video under 5 minutes
```

---

## Summary

### Training Commands:
1. **Preprocess**: `python3 scripts/preprocess_data.py data.csv processed_data`
2. **Train Local**: `python3 scripts/train_local.py --data-dir processed_data --model-dir models`
3. **Train AWS**: `python3 scripts/sagemaker_train.py --bucket newsverify-models ...`

### Showcase Steps:
1. **Start App**: `python3 application.py`
2. **Open Browser**: `http://localhost:5000`
3. **Test Examples**: Use prepared headlines
4. **Explain Results**: Show confidence scores and probabilities
5. **Discuss Technical**: Mention accuracy, features, architecture

**Good luck with your presentation!** 🎯

