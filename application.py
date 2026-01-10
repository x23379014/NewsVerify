"""
Main application entry point for Elastic Beanstalk
"""

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5001, debug=False)

