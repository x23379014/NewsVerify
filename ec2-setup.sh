#!/bin/bash
# EC2 Setup Script for NewsVerify
# Run this script on a fresh EC2 instance (Amazon Linux or Ubuntu)

set -e

echo "🚀 Setting up NewsVerify on EC2..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

echo "📦 Detected OS: $OS"

# Update system
if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ]; then
    echo "📥 Updating Amazon Linux..."
    sudo yum update -y
    sudo yum install -y python3.9 python3.9-pip git gcc gcc-c++ make
elif [ "$OS" = "ubuntu" ]; then
    echo "📥 Updating Ubuntu..."
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get install -y python3.9 python3.9-pip python3.9-venv git build-essential
else
    echo "❌ Unsupported OS: $OS"
    exit 1
fi

# Create application directory
APP_DIR="/home/ec2-user/newsverify"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3.9 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (if requirements.txt exists)
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found. Installing basic dependencies..."
    pip install flask gunicorn boto3 pandas numpy scikit-learn xgboost nltk textblob joblib
fi

# Download NLTK data
echo "📚 Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True)" || true

# Create .env file
echo "⚙️  Creating environment file..."
cat > $APP_DIR/.env << EOF
S3_BUCKET=newsverify-models-2026
MODEL_KEY=models/model.pkl
VECTORIZER_KEY=models/tfidf_vectorizer.pkl
LABEL_ENCODER_KEY=models/label_encoder.pkl
STAT_FEATURES_KEY=models/stat_feature_names.pkl
AWS_DEFAULT_REGION=us-east-1
FLASK_ENV=production
EOF

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Upload your application files to: $APP_DIR"
echo "2. Set up Gunicorn service (see EC2_DEPLOYMENT_GUIDE.md)"
echo "3. Configure Nginx (see EC2_DEPLOYMENT_GUIDE.md)"
echo "4. Start the application"
