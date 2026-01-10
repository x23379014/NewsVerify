"""
SageMaker Training Script for XGBoost Model
This script is used by SageMaker to train the model
"""

import argparse
import os
import joblib
import numpy as np
import xgboost as xgb
from scipy.sparse import load_npz
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import json

def load_data(base_dir):
    """Load preprocessed data"""
    X_train = load_npz(os.path.join(base_dir, 'X_train.npz'))
    X_val = load_npz(os.path.join(base_dir, 'X_val.npz'))
    X_test = load_npz(os.path.join(base_dir, 'X_test.npz'))
    
    y_train = np.load(os.path.join(base_dir, 'y_train.npy'))
    y_val = np.load(os.path.join(base_dir, 'y_val.npy'))
    y_test = np.load(os.path.join(base_dir, 'y_test.npy'))
    
    return X_train, X_val, X_test, y_train, y_val, y_test

def evaluate_model(model, X, y, set_name):
    """Evaluate model and return metrics"""
    y_pred = model.predict(X)
    
    accuracy = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y, y_pred, average='weighted', zero_division=0)
    
    print(f"\n{set_name} Set Metrics:")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    
    return {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1)
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    # SageMaker environment variables
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAINING'))
    parser.add_argument('--validation', type=str, default=os.environ.get('SM_CHANNEL_VALIDATION'))
    parser.add_argument('--test', type=str, default=os.environ.get('SM_CHANNEL_TEST'))
    
    # Hyperparameters
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--eta', type=float, default=0.3)
    parser.add_argument('--min-child-weight', type=int, default=1)
    parser.add_argument('--subsample', type=float, default=0.8)
    parser.add_argument('--colsample-bytree', type=float, default=0.8)
    parser.add_argument('--num-round', type=int, default=100)
    parser.add_argument('--objective', type=str, default='binary:logistic')
    parser.add_argument('--eval-metric', type=str, default='logloss')
    
    args = parser.parse_args()
    
    # Load data
    print("Loading data...")
    X_train, X_val, X_test, y_train, y_val, y_test = load_data(args.train)
    
    print(f"Training set shape: {X_train.shape}")
    print(f"Validation set shape: {X_val.shape}")
    print(f"Test set shape: {X_test.shape}")
    
    # Train XGBoost model
    print("\nTraining XGBoost model...")
    model = xgb.XGBClassifier(
        max_depth=args.max_depth,
        eta=args.eta,
        min_child_weight=args.min_child_weight,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        n_estimators=args.num_round,
        objective=args.objective,
        eval_metric=args.eval_metric,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=True
    )
    
    # Evaluate
    print("\nEvaluating model...")
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    # Save model
    model_path = os.path.join(args.model_dir, 'model.pkl')
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Save metrics
    metrics = {
        'train': train_metrics,
        'validation': val_metrics,
        'test': test_metrics
    }
    
    metrics_path = os.path.join(args.model_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Metrics saved to {metrics_path}")
    
    # Save feature importance
    feature_importance = model.feature_importances_
    importance_path = os.path.join(args.model_dir, 'feature_importance.npy')
    np.save(importance_path, feature_importance)
    print(f"Feature importance saved to {importance_path}")

