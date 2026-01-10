#!/bin/bash
# Script to run SageMaker training using Python script (handles .npz files)

cd /Users/nikhiltamatta/Desktop/NewsVerify

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run SageMaker training
python scripts/sagemaker_train.py \
    --bucket newsverify-models-2026 \
    --data-path processed_data \
    --instance-type ml.m4.xlarge \
    --role arn:aws:iam::587821825538:role/SageMakerExecutionRole
