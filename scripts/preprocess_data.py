"""
Data Preprocessing Script for Fake News Detection
This script performs EDA, cleaning, and feature engineering
"""

import pandas as pd
import numpy as np
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os
from urllib.parse import urlparse

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Initialize
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    """Clean and preprocess text"""
    if pd.isna(text):
        return ""
    
    # Convert to string and lowercase
    text = str(text).lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and lemmatize
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and len(word) > 2]
    
    return ' '.join(tokens)

def extract_statistical_features(df):
    """Extract statistical features from text"""
    features = pd.DataFrame()
    
    # Headline features
    features['headline_length'] = df['Headline'].astype(str).str.len()
    features['headline_word_count'] = df['Headline'].astype(str).str.split().str.len()
    features['headline_uppercase_ratio'] = df['Headline'].astype(str).apply(
        lambda x: sum(1 for c in x if c.isupper()) / len(x) if len(x) > 0 else 0
    )
    features['headline_punctuation_count'] = df['Headline'].astype(str).str.count(r'[^\w\s]')
    
    # Body features
    features['body_length'] = df['Body'].astype(str).str.len()
    features['body_word_count'] = df['Body'].astype(str).str.split().str.len()
    features['body_sentence_count'] = df['Body'].astype(str).str.count(r'[.!?]+')
    features['body_avg_word_length'] = df['Body'].astype(str).apply(
        lambda x: np.mean([len(word) for word in x.split()]) if len(x.split()) > 0 else 0
    )
    features['body_punctuation_count'] = df['Body'].astype(str).str.count(r'[^\w\s]')
    features['body_exclamation_count'] = df['Body'].astype(str).str.count('!')
    features['body_question_count'] = df['Body'].astype(str).str.count(r'\?')
    
    # URL features
    features['url_length'] = df['URLs'].astype(str).str.len()
    features['has_url'] = df['URLs'].astype(str).apply(lambda x: 1 if 'http' in str(x).lower() else 0)
    
    # Combined features
    features['total_length'] = features['headline_length'] + features['body_length']
    features['headline_body_ratio'] = features['headline_length'] / (features['body_length'] + 1)
    
    return features

def preprocess_data(input_path, output_dir='processed_data'):
    """Main preprocessing function"""
    print("Loading data...")
    df = pd.read_csv(input_path)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Label distribution:\n{df['Label'].value_counts()}")
    
    # Handle missing values
    df['Headline'] = df['Headline'].fillna('')
    df['Body'] = df['Body'].fillna('')
    df['URLs'] = df['URLs'].fillna('')
    
    # Clean text
    print("Cleaning text...")
    df['Headline_cleaned'] = df['Headline'].apply(clean_text)
    df['Body_cleaned'] = df['Body'].apply(clean_text)
    
    # Combine headline and body for TF-IDF
    df['Combined_text'] = df['Headline_cleaned'] + ' ' + df['Body_cleaned']
    
    # Extract statistical features
    print("Extracting statistical features...")
    stat_features = extract_statistical_features(df)
    
    # TF-IDF Vectorization
    print("Creating TF-IDF features...")
    tfidf_vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95
    )
    
    tfidf_features = tfidf_vectorizer.fit_transform(df['Combined_text'])
    
    # Combine TF-IDF and statistical features
    from scipy.sparse import hstack
    X = hstack([tfidf_features, stat_features.values])
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df['Label'])
    
    # Train/Val/Test split
    print("Splitting data...")
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.2, random_state=42, stratify=y_temp
    )
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save processed data
    print("Saving processed data...")
    from scipy.sparse import save_npz
    save_npz(f'{output_dir}/X_train.npz', X_train)
    save_npz(f'{output_dir}/X_val.npz', X_val)
    save_npz(f'{output_dir}/X_test.npz', X_test)
    
    np.save(f'{output_dir}/y_train.npy', y_train)
    np.save(f'{output_dir}/y_val.npy', y_val)
    np.save(f'{output_dir}/y_test.npy', y_test)
    
    # Save vectorizer and encoders
    joblib.dump(tfidf_vectorizer, f'{output_dir}/tfidf_vectorizer.pkl')
    joblib.dump(label_encoder, f'{output_dir}/label_encoder.pkl')
    joblib.dump(stat_features.columns.tolist(), f'{output_dir}/stat_feature_names.pkl')
    
    print(f"\nPreprocessing complete!")
    print(f"Train set: {X_train.shape[0]} samples")
    print(f"Validation set: {X_val.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    print(f"Total features: {X_train.shape[1]}")
    
    return output_dir

if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data.csv'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'processed_data'
    
    preprocess_data(input_file, output_dir)

