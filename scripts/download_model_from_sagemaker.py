"""
Download trained model from SageMaker to S3 for Elastic Beanstalk
"""

import boto3
import os
import argparse

def download_model_from_sagemaker(
    s3_bucket,
    model_artifact_path,
    local_output_dir='models'
):
    """
    Download model artifacts from SageMaker to local directory
    
    Args:
        s3_bucket: S3 bucket name
        model_artifact_path: S3 path to model artifacts (from SageMaker training job)
        local_output_dir: Local directory to save models
    """
    
    s3_client = boto3.client('s3')
    
    # Parse S3 path
    if model_artifact_path.startswith('s3://'):
        model_artifact_path = model_artifact_path[5:]
    
    bucket, key_prefix = model_artifact_path.split('/', 1)
    
    # Create local directory
    os.makedirs(local_output_dir, exist_ok=True)
    
    # List and download model files
    print(f"Downloading model from s3://{bucket}/{key_prefix}")
    
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=key_prefix)
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                filename = os.path.basename(key)
                
                # Download model.pkl, metrics.json, etc.
                if filename in ['model.pkl', 'metrics.json', 'feature_importance.npy']:
                    local_path = os.path.join(local_output_dir, filename)
                    print(f"Downloading {filename}...")
                    s3_client.download_file(bucket, key, local_path)
                    print(f"Saved to {local_path}")
    
    print(f"\nModel downloaded to {local_output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', type=str, required=True,
                       help='S3 bucket name')
    parser.add_argument('--model-path', type=str, required=True,
                       help='S3 path to model artifacts')
    parser.add_argument('--output-dir', type=str, default='models',
                       help='Local output directory')
    
    args = parser.parse_args()
    
    download_model_from_sagemaker(
        s3_bucket=args.bucket,
        model_artifact_path=args.model_path,
        local_output_dir=args.output_dir
    )

