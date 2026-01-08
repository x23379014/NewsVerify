"""
Routes for the Fake News Detection Application
"""

from flask import Blueprint, render_template, request, jsonify
import logging
import os
import joblib
import numpy as np
from scipy.sparse import hstack
import boto3
from botocore.exceptions import ClientError
import re
from urllib.parse import urlparse

# Import preprocessing functions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.preprocess_data import clean_text, extract_statistical_features

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# Initialize AWS clients (with error handling for local development)
# Get AWS region from environment variable, default to us-east-1
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', os.environ.get('AWS_REGION', 'us-east-1'))

try:
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
except Exception as e:
    logger.warning(f"AWS clients not initialized (running locally?): {e}")
    s3_client = None
    cloudwatch = None

# S3 Configuration
S3_BUCKET = os.environ.get('S3_BUCKET', 'newsverify-models')
MODEL_KEY = os.environ.get('MODEL_KEY', 'models/model.pkl')
VECTORIZER_KEY = os.environ.get('VECTORIZER_KEY', 'models/tfidf_vectorizer.pkl')
LABEL_ENCODER_KEY = os.environ.get('LABEL_ENCODER_KEY', 'models/label_encoder.pkl')
STAT_FEATURES_KEY = os.environ.get('STAT_FEATURES_KEY', 'models/stat_feature_names.pkl')

# Load model and preprocessors (lazy loading)
model = None
tfidf_vectorizer = None
label_encoder = None
stat_feature_names = None

def load_model_local():
    """Load model and preprocessors from local directory"""
    global model, tfidf_vectorizer, label_encoder, stat_feature_names
    
    try:
        # Try local models directory first
        local_model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        
        model_path = os.path.join(local_model_dir, 'model.pkl')
        vectorizer_path = os.path.join(local_model_dir, 'tfidf_vectorizer.pkl')
        encoder_path = os.path.join(local_model_dir, 'label_encoder.pkl')
        features_path = os.path.join(local_model_dir, 'stat_feature_names.pkl')
        
        if all(os.path.exists(p) for p in [model_path, vectorizer_path, encoder_path, features_path]):
            logger.info("Loading model from local directory...")
            model = joblib.load(model_path)
            tfidf_vectorizer = joblib.load(vectorizer_path)
            label_encoder = joblib.load(encoder_path)
            stat_feature_names = joblib.load(features_path)
            logger.info("Model and preprocessors loaded successfully from local directory")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error loading model from local: {e}")
        return False

def load_model_from_s3():
    """Load model and preprocessors from S3"""
    global model, tfidf_vectorizer, label_encoder, stat_feature_names
    
    try:
        # Create local directory for models
        local_model_dir = '/tmp/models'
        os.makedirs(local_model_dir, exist_ok=True)
        
        # Download from S3
        model_path = os.path.join(local_model_dir, 'model.pkl')
        vectorizer_path = os.path.join(local_model_dir, 'tfidf_vectorizer.pkl')
        encoder_path = os.path.join(local_model_dir, 'label_encoder.pkl')
        features_path = os.path.join(local_model_dir, 'stat_feature_names.pkl')
        
        if not os.path.exists(model_path):
            logger.info(f"Downloading model from s3://{S3_BUCKET}/{MODEL_KEY}")
            s3_client.download_file(S3_BUCKET, MODEL_KEY, model_path)
        
        if not os.path.exists(vectorizer_path):
            logger.info(f"Downloading vectorizer from s3://{S3_BUCKET}/{VECTORIZER_KEY}")
            s3_client.download_file(S3_BUCKET, VECTORIZER_KEY, vectorizer_path)
        
        if not os.path.exists(encoder_path):
            logger.info(f"Downloading label encoder from s3://{S3_BUCKET}/{LABEL_ENCODER_KEY}")
            s3_client.download_file(S3_BUCKET, LABEL_ENCODER_KEY, encoder_path)
        
        if not os.path.exists(features_path):
            logger.info(f"Downloading feature names from s3://{S3_BUCKET}/{STAT_FEATURES_KEY}")
            s3_client.download_file(S3_BUCKET, STAT_FEATURES_KEY, features_path)
        
        # Load models
        model = joblib.load(model_path)
        tfidf_vectorizer = joblib.load(vectorizer_path)
        label_encoder = joblib.load(encoder_path)
        stat_feature_names = joblib.load(features_path)
        
        logger.info("Model and preprocessors loaded successfully from S3")
        return True
        
    except ClientError as e:
        logger.error(f"Error loading model from S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def log_to_cloudwatch(metric_name, value, unit='Count'):
    """Log metrics to CloudWatch"""
    try:
        if cloudwatch:
            cloudwatch.put_metric_data(
                Namespace='NewsVerify',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit
                    }
                ]
            )
    except Exception as e:
        logger.warning(f"Failed to log to CloudWatch: {e}")

@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/predict', methods=['POST'])
def predict():
    """Predict endpoint"""
    global model, tfidf_vectorizer, label_encoder, stat_feature_names
    
    try:
        # Load model if not loaded (try local first, then S3)
        if model is None:
            if not load_model_local():
                if not load_model_from_s3():
                    return jsonify({
                        'error': 'Model not available. Please ensure model is trained and available locally or in S3.'
                    }), 500
        
        # Get input data
        data = request.get_json()
        headline = data.get('headline', '')
        body = data.get('body', '')
        url = data.get('url', '')
        
        if not headline and not body:
            return jsonify({'error': 'Please provide at least headline or body text'}), 400
        
        logger.info(f"Received prediction request - Headline: {headline[:50]}...")
        
        # Preprocess text
        headline_cleaned = clean_text(headline)
        body_cleaned = clean_text(body)
        combined_text = headline_cleaned + ' ' + body_cleaned
        
        # Create DataFrame for statistical features
        import pandas as pd
        df_temp = pd.DataFrame({
            'Headline': [headline],
            'Body': [body],
            'URLs': [url]
        })
        
        # Extract statistical features
        stat_features = extract_statistical_features(df_temp)
        
        # Ensure feature order matches training
        stat_features = stat_features[stat_feature_names]
        
        # TF-IDF transformation
        tfidf_features = tfidf_vectorizer.transform([combined_text])
        
        # Combine features
        X = hstack([tfidf_features, stat_features.values])
        
        # Predict
        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0]
        
        # Decode label - ensure native Python types (convert all numpy types)
        prediction = int(prediction)  # Convert numpy int64 to Python int
        label_array = label_encoder.inverse_transform([prediction])
        label = str(label_array[0])  # Ensure string, handle numpy string types
        confidence = float(max(probability))
        
        # Convert probability array to native Python floats
        prob_fake = float(probability[0]) if len(probability) > 0 else 0.0
        prob_real = float(probability[1]) if len(probability) > 1 else 0.0
        
        # Log to CloudWatch
        log_to_cloudwatch('Predictions', 1)
        log_to_cloudwatch('Confidence', confidence, 'None')
        
        result = {
            'prediction': label,
            'confidence': confidence,
            'probabilities': {
                'fake': prob_fake,
                'real': prob_real
            }
        }
        
        logger.info(f"Prediction: {label} (confidence: {confidence:.2f})")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        log_to_cloudwatch('PredictionErrors', 1)
        return jsonify({'error': str(e)}), 500

@main.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

