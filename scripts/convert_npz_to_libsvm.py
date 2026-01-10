"""
Convert .npz sparse matrices to LibSVM format for SageMaker built-in XGBoost
LibSVM format is more efficient than CSV for sparse data
"""

import numpy as np
from scipy.sparse import load_npz
import os
import sys

def convert_npz_to_libsvm(npz_path, labels_path, output_path):
    """
    Convert sparse matrix (.npz) to LibSVM format
    
    LibSVM format: label index1:value1 index2:value2 ...
    Example: 1 1:0.5 3:0.2 5:0.8
    """
    print(f"Loading {npz_path}...")
    X = load_npz(npz_path)
    y = np.load(labels_path)
    
    print(f"Matrix shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    
    # Convert to dense if needed (for LibSVM, we can use sparse representation)
    # LibSVM format only includes non-zero features
    print(f"Writing to {output_path}...")
    
    with open(output_path, 'w') as f:
        for i in range(X.shape[0]):
            # Get label
            label = int(y[i])
            
            # Get non-zero features
            row = X.getrow(i)
            non_zero_indices = row.indices
            non_zero_values = row.data
            
            # Format: label index1:value1 index2:value2 ...
            # Note: LibSVM uses 1-based indexing
            line = f"{label}"
            for idx, val in zip(non_zero_indices, non_zero_values):
                line += f" {idx + 1}:{val}"
            line += "\n"
            
            f.write(line)
            
            if (i + 1) % 1000 == 0:
                print(f"Processed {i + 1}/{X.shape[0]} samples...")
    
    print(f"Conversion complete! Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_npz_to_libsvm.py <input_dir> <output_dir>")
        print("Example: python convert_npz_to_libsvm.py processed_data processed_data_libsvm")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f"{input_dir}_libsvm"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert train, val, test sets
    print("Converting training set...")
    convert_npz_to_libsvm(
        os.path.join(input_dir, 'X_train.npz'),
        os.path.join(input_dir, 'y_train.npy'),
        os.path.join(output_dir, 'train.libsvm')
    )
    
    print("\nConverting validation set...")
    convert_npz_to_libsvm(
        os.path.join(input_dir, 'X_val.npz'),
        os.path.join(input_dir, 'y_val.npy'),
        os.path.join(output_dir, 'validation.libsvm')
    )
    
    print("\nConverting test set...")
    convert_npz_to_libsvm(
        os.path.join(input_dir, 'X_test.npz'),
        os.path.join(input_dir, 'y_test.npy'),
        os.path.join(output_dir, 'test.libsvm')
    )
    
    print("\n✅ All conversions complete!")
    print(f"LibSVM files saved in: {output_dir}")
    print("\nNext steps:")
    print(f"1. Upload to S3: aws s3 cp {output_dir}/ s3://newsverify-models-2026/training_data_libsvm/ --recursive")
    print("2. Use 'libsvm' as content type in SageMaker console")
