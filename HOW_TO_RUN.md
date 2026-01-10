# How to Run NewsVerify Project

This guide shows you how to run the NewsVerify fake news detection system locally and on AWS.

---

## 🚀 Quick Start (Local Development)

### Step 1: Activate Virtual Environment

```bash
cd /Users/nikhiltamatta/Desktop/NewsVerify

# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows
```

### Step 2: Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt

# Download NLTK data (required for text processing)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab', quiet=True)"
```

### Step 3: Run the Application

```bash
python application.py
```

The application will start on: **http://localhost:5001** (port changed to avoid macOS AirPlay conflict on port 5000)

### Step 4: Open in Browser

Open your browser and go to: **http://localhost:5001**

You should see the NewsVerify web interface where you can:
- Enter a news headline
- Optionally add article body and URL
- Click "Verify News" to get a prediction

---

## 📋 Detailed Setup Instructions

### Prerequisites

1. **Python 3.8+** installed
2. **Virtual environment** (already created in `venv/`)
3. **Model files** (already present in `models/` directory)

### Check Your Setup

```bash
# Check Python version
python --version  # Should be 3.8 or higher

# Check if models exist
ls models/
# Should show: model.pkl, tfidf_vectorizer.pkl, label_encoder.pkl, stat_feature_names.pkl
```

---

## 🎯 Running Different Components

### 1. Run Web Application (Flask)

```bash
# Activate venv
source venv/bin/activate

# Run Flask app
python application.py

# Or with debug mode (for development)
python -c "from app import create_app; app = create_app(); app.run(debug=True, host='0.0.0.0', port=5001)"
```

**Access at:** http://localhost:5001 (port changed to avoid macOS AirPlay conflict)

### 2. Test API Endpoint Directly

```bash
# Test health endpoint
curl http://localhost:5001/health

# Test prediction endpoint
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Breaking: Scientists discover new planet",
    "body": "Scientists have discovered a new planet in a distant galaxy...",
    "url": "https://example.com/news"
  }'
```

### 3. Preprocess Data (if needed)

```bash
# Preprocess the dataset
python scripts/preprocess_data.py data.csv processed_data
```

### 4. Train Model Locally

```bash
# Train model using local data
python scripts/train_local.py
```

### 5. Train Model on SageMaker

```bash
# Using the script
python scripts/sagemaker_train.py \
    --bucket newsverify-models-2026 \
    --data-path processed_data \
    --instance-type ml.m4.xlarge \
    --role arn:aws:iam::587821825538:role/SageMakerExecutionRole

# Or use the shell script
chmod +x run_sagemaker_training.sh
./run_sagemaker_training.sh
```

---

## 🌐 Running on AWS (EC2)

### Prerequisites

1. AWS account configured
2. AWS CLI installed and configured
3. EC2 instance created
4. IAM role with S3 permissions attached to EC2

### Deploy to EC2

**Quick Summary:**

1. **Create EC2 Instance**
   - Go to EC2 Console → Launch Instance
   - Choose: Amazon Linux 2023
   - Instance type: `t3.medium` (recommended), or `t3.large` for higher performance
   - Security group: Allow SSH (22) and HTTP (80)
   - Attach IAM role with S3 read permissions

2. **Set Up Application on EC2**
   ```bash
   # SSH into instance
   ssh -i your-key.pem ec2-user@<EC2_IP>
   
   # Install Python, Nginx, and dependencies
   sudo dnf install python3.9 python3-pip nginx -y
   
   # Navigate to application directory
   cd /home/ec2-user/newsverify
   
   # Create virtual environment
   python3.9 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Download NLTK data
   python -c "import nltk; nltk.download('punkt_tab', quiet=True)"
   
   # Fix permissions for static files
   chmod 755 /home/ec2-user/
   chmod 644 /home/ec2-user/newsverify/app/static/*
   ```

3. **Configure Gunicorn and Nginx**
   - Create systemd service for Gunicorn
   - Configure Nginx as reverse proxy
   - Ensure `/static` location block comes before `/` in Nginx config

4. **Start Services**
   ```bash
   # On EC2 instance
   sudo systemctl start newsverify
   sudo systemctl enable newsverify
   sudo systemctl start nginx
   sudo systemctl enable nginx
   ```

5. **Test Application**
   ```bash
   # Test health endpoint
   curl http://<EC2_IP>/health
   
   # Test static files
   curl http://<EC2_IP>/static/style.css
   ```

**Important Notes:**
- Model files are automatically loaded from S3 bucket: `newsverify-models-2026`
- Ensure `/home/ec2-user/` has `755` permissions for Nginx to access static files
- Static files should be at `/home/ec2-user/newsverify/app/static/`

---

## 🔧 Troubleshooting

### Issue: "Model not available" Error

**Solution:** Make sure model files exist in `models/` directory:
```bash
ls models/
# Should show: model.pkl, tfidf_vectorizer.pkl, label_encoder.pkl, stat_feature_names.pkl
```

If missing, either:
1. Train locally: `python scripts/train_local.py`
2. Download from S3 (if deployed): Check S3 bucket

### Issue: Import Errors

**Solution:** Install missing dependencies:
```bash
pip install -r requirements.txt
```

### Issue: NLTK Data Missing

**Solution:** Download NLTK data:
```bash
# For local development
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab', quiet=True)"

# For EC2 deployment
python -c "import nltk; nltk.download('punkt_tab', quiet=True)"
```

### Issue: Port Already in Use

**Solution:** The application now uses port 5001 by default to avoid macOS AirPlay conflict. If you need to change it:
```bash
# Edit application.py, change port from 5001 to another port
# Or kill the process using the port
lsof -ti:5001 | xargs kill  # Mac/Linux
```

### Issue: AWS Credentials Not Found

**Solution:** Configure AWS CLI:
```bash
aws configure
# Enter your Access Key ID, Secret Access Key, region, and output format
```

### Issue: Static Files (CSS/JS) Not Loading on EC2

**Solution:** Fix permissions and Nginx configuration:
```bash
# Fix parent directory permissions
chmod 755 /home/ec2-user/

# Fix file permissions
chmod 644 /home/ec2-user/newsverify/app/static/*

# Ensure Nginx config has /static location before / location
# Test static file access
curl http://localhost/static/style.css

# Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

---

## 📊 Testing the Application

### Test Cases

1. **Real News Example:**
   ```json
   {
     "headline": "Scientists discover new exoplanet",
     "body": "Astronomers have identified a new planet in the habitable zone...",
     "url": "https://www.nasa.gov/news"
   }
   ```

2. **Fake News Example:**
   ```json
   {
     "headline": "BREAKING: Government hiding aliens in secret facility!",
     "body": "Shocking revelation about secret government programs...",
     "url": "https://conspiracy-site.com"
   }
   ```

### Expected Response

```json
{
  "prediction": "REAL" or "FAKE",
  "confidence": 0.95,
  "probabilities": {
    "fake": 0.05,
    "real": 0.95
  }
}
```

---

## 🎨 Web Interface Features

The web interface (`http://localhost:5001` for local, or `http://<EC2_IP>` for production) includes:

- **Headline Input** (required)
- **Body Text Input** (optional)
- **URL Input** (optional)
- **Verify Button** - Gets prediction
- **Results Display** - Shows prediction, confidence, and probabilities

---

## 📝 Environment Variables (Optional)

For local development, you can set these (optional):

```bash
export S3_BUCKET=newsverify-models-2026
export MODEL_KEY=models/model.pkl
export VECTORIZER_KEY=models/tfidf_vectorizer.pkl
export LABEL_ENCODER_KEY=models/label_encoder.pkl
export STAT_FEATURES_KEY=models/stat_feature_names.pkl
export AWS_DEFAULT_REGION=us-east-1
```

Or create a `.env` file (not tracked in git):
```
S3_BUCKET=newsverify-models-2026
MODEL_KEY=models/model.pkl
VECTORIZER_KEY=models/tfidf_vectorizer.pkl
LABEL_ENCODER_KEY=models/label_encoder.pkl
STAT_FEATURES_KEY=models/stat_feature_names.pkl
AWS_DEFAULT_REGION=us-east-1
```

---

## 🚀 Production Deployment

For production, use:

1. **Gunicorn** (already in requirements.txt):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 application:application
   ```

2. **EC2** (recommended):
   - Use Gunicorn + Nginx on EC2 instance
   - See "Running on AWS (EC2)" section above for deployment steps

3. **Docker** (if containerizing):
   ```bash
   docker build -t newsverify .
   docker run -p 5000:5000 newsverify
   ```

---

## 📚 Next Steps

1. **Train a new model**: Use `scripts/train_local.py` or SageMaker
2. **Improve accuracy**: Modify preprocessing in `scripts/preprocess_data.py`
3. **Add features**: Update feature extraction in `app/routes.py`
4. **Deploy to AWS**: Follow EC2 deployment steps in this guide

## 🔄 Recent Changes

- **Port Configuration**: Local development now uses port 5001 (to avoid macOS AirPlay conflict)
- **S3 Bucket**: Updated to `newsverify-models-2026`
- **SageMaker Instance**: Using `ml.m4.xlarge` (Free Tier alternative)
- **EC2 Deployment**: Successfully deployed with Nginx and Gunicorn
- **NLTK Data**: Added `punkt_tab` resource for compatibility
- **Static Files**: Configured Nginx to serve static files correctly

---

## 🆘 Need Help?

- Check logs: Application logs will show in terminal
- Check model files: Ensure all `.pkl` files exist in `models/`
- Check dependencies: Run `pip list` to see installed packages
- Check AWS: Verify S3 bucket and IAM permissions if using AWS

---

**Happy coding! 🎉**
