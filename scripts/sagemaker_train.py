"""
Script to train model using SageMaker
This script uploads data to S3 and creates a SageMaker training job
"""

import boto3
import sagemaker
from sagemaker.xgboost.estimator import XGBoost
from sagemaker import get_execution_role
import os
import json
from datetime import datetime

def train_on_sagemaker(
    s3_bucket='newsverify-models',
    training_data_path='processed_data',
    role=None,
    instance_type='ml.m5.xlarge',
    instance_count=1
):
    """
    Train XGBoost model on SageMaker
    
    Args:
        s3_bucket: S3 bucket name
        training_data_path: Local path to processed data
        role: IAM role for SageMaker (if None, will try to get default)
        instance_type: EC2 instance type for training
        instance_count: Number of instances
    """
    
    # Initialize SageMaker session
    sess = sagemaker.Session()
    
    # Get IAM role
    if role is None:
        try:
            role = get_execution_role()
        except:
            role = input("Please provide SageMaker execution role ARN: ")
    
    # Upload data to S3
    print("Uploading data to S3...")
    s3_data_path = f's3://{s3_bucket}/training_data'
    
    sess.upload_data(
        path=training_data_path,
        bucket=s3_bucket,
        key_prefix='training_data'
    )
    
    print(f"Data uploaded to {s3_data_path}")
    
    # Create XGBoost estimator
    xgb_estimator = XGBoost(
        entry_point='train_sagemaker.py',
        source_dir='scripts',
        role=role,
        instance_type=instance_type,
        instance_count=instance_count,
        framework_version='1.7-1',
        py_version='py3',
        hyperparameters={
            'max-depth': 6,
            'eta': 0.3,
            'min-child-weight': 1,
            'subsample': 0.8,
            'colsample-bytree': 0.8,
            'num-round': 100,
            'objective': 'binary:logistic',
            'eval-metric': 'logloss'
        }
    )
    
    # Define input data channels
    # Note: content_type doesn't matter here because train_sagemaker.py loads .npz files directly
    train_input = sagemaker.inputs.TrainingInput(
        s3_data=f'{s3_data_path}',
        content_type='application/x-npz'  # Changed to match actual data format
    )
    
    # Start training job
    print("Starting training job...")
    xgb_estimator.fit({'training': train_input})
    
    # Deploy model (optional - can be done separately)
    print("\nTraining completed!")
    print(f"Model artifacts saved to: {xgb_estimator.model_data}")
    
    return xgb_estimator

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', type=str, default='newsverify-models',
                       help='S3 bucket name')
    parser.add_argument('--data-path', type=str, default='processed_data',
                       help='Local path to processed data')
    parser.add_argument('--instance-type', type=str, default='ml.m4.xlarge',
                       help='EC2 instance type for training')
    parser.add_argument('--role', type=str, default=None,
                       help='SageMaker execution role ARN')
    
    args = parser.parse_args()
    
    train_on_sagemaker(
        s3_bucket=args.bucket,
        training_data_path=args.data_path,
        instance_type=args.instance_type,
        role=args.role
    )

