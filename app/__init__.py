"""
Flask Application for Fake News Detection
"""

from flask import Flask
from flask.json.provider import DefaultJSONProvider
import logging
import boto3
from botocore.exceptions import ClientError
import numpy as np

class NumpyJSONProvider(DefaultJSONProvider):
    """Custom JSON provider to handle numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int_)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float_)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, np.str_):
            return str(obj)
        return super().default(obj)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Set custom JSON provider for Flask 2.2+
    app.json = NumpyJSONProvider(app)
    
    # Configure logging to CloudWatch
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.INFO)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app

