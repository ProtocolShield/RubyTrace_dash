#!/usr/bin/env python3
"""
VPS Setup Script for OSINT Platform
Run this script on your VPS after deploying the code to download required NLTK data.
"""

import os
import sys
import nltk
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_nltk_data():
    """Download required NLTK data for the OSINT platform"""
    try:
        # Create NLTK data directory
        nltk_data_dir = os.path.expanduser('~/nltk_data')  # Adjusted from /home/runner
        os.makedirs(nltk_data_dir, exist_ok=True)

        # Set NLTK data path
        nltk.data.path.append(nltk_data_dir)

        # Download required NLTK data
        required_datasets = [
            'punkt',           # Sentence tokenizer
            'stopwords',       # Stop words
            'wordnet',         # WordNet lexical database
            'averaged_perceptron_tagger',  # POS tagger
            'vader_lexicon',   # Sentiment analysis
            'brown',           # Brown corpus
            'omw-1.4'          # Open Multilingual Wordnet
        ]

        logging.info("Starting NLTK data download...")

        for dataset in required_datasets:
            try:
                logging.info(f"Downloading {dataset}...")
                nltk.download(dataset, download_dir=nltk_data_dir)
                logging.info(f"✓ {dataset} downloaded successfully")
            except Exception as e:
                logging.warning(f"Failed to download {dataset}: {e}")

        # Test TextBlob functionality
        try:
            from textblob import TextBlob
            test_text = "This is a test for privacy and security analysis."
            blob = TextBlob(test_text)
            blob.noun_phrases  # Triggers corpus use
            logging.info("✓ TextBlob functionality verified")
        except Exception as e:
            logging.warning(f"TextBlob test failed: {e}")
            logging.info("Running TextBlob corpus download...")
            os.system("python -m textblob.download_corpora")

        logging.info("NLTK setup completed successfully!")
        return True

    except Exception as e:
        logging.error(f"NLTK setup failed: {e}")
        return False

def setup_environment():
    """Set up environment variables and configurations"""
    try:
        # Create required directories
        directories = [
            'data',
            'logs',
            'static/uploads'
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logging.info(f"✓ Created directory: {directory}")

        logging.info("Environment setup completed!")
        return True

    except Exception as e:
        logging.error(f"Environment setup failed: {e}")
        return False

def setup_tor():
    """Set up Tor service and configuration"""
    try:
        logging.info("Setting up Tor service...")

        # Check if Tor is installed and running
        import subprocess
        result = subprocess.run(['systemctl', 'is-active', 'tor'],
                              capture_output=True, text=True)

        if result.returncode != 0:
            logging.warning("Tor service not running. Installing Tor...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'tor'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'tor'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'tor'], check=True)
        else:
            logging.info("✓ Tor service is already running")

        # Test Tor connection
        try:
            import requests
            import time
            time.sleep(5)  # Wait for Tor to be ready

            # Test connection through Tor
            proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }

            response = requests.get('https://check.torproject.org/api/ip',
                                  proxies=proxies, timeout=30)
            data = response.json()

            if data.get('IsTor'):
                logging.info(f"✓ Tor connection verified. Exit IP: {data.get('IP')}")
            else:
                logging.warning("Tor connection test failed - not routing through Tor")

        except Exception as e:
            logging.warning(f"Tor connection test failed: {e}")

        return True

    except Exception as e:
        logging.error(f"Tor setup failed: {e}")
        return False

def setup_postgresql():
    """Set up PostgreSQL database"""
    try:
        logging.info("Setting up PostgreSQL database...")

        import subprocess

        # Check if PostgreSQL is installed and running
        result = subprocess.run(['systemctl', 'is-active', 'postgresql'],
                              capture_output=True, text=True)

        if result.returncode != 0:
            logging.info("Installing PostgreSQL...")
            subprocess.run(['sudo', 'apt', 'install', '-y', 'postgresql', 'postgresql-contrib'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'postgresql'], check=True)

        # Create database and user
        logging.info("Creating database and user...")
        psql_commands = [
            "CREATE USER osint_user WITH PASSWORD 'secure_password_2024';",
            "CREATE DATABASE osint_db OWNER osint_user;",
            "GRANT ALL PRIVILEGES ON DATABASE osint_db TO osint_user;",
            "\\c osint_db",
            "GRANT ALL ON SCHEMA public TO osint_user;",
            "ALTER USER osint_user CREATEDB;"
        ]

        for command in psql_commands:
            try:
                subprocess.run(['sudo', '-u', 'postgres', 'psql', '-c', command],
                             check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                if "already exists" in str(e.stderr) or "already exists" in str(e.stdout):
                    logging.info(f"Database element already exists: {command[:50]}...")
                else:
                    logging.warning(f"Command may have failed: {command[:50]}...")

        logging.info("✓ PostgreSQL setup completed")
        logging.info("Database: postgresql://osint_user:secure_password_2024@localhost:5432/osint_db")
        return True

    except Exception as e:
        logging.error(f"PostgreSQL setup failed: {e}")
        return False

def main():
    """Main setup function"""
    logging.info("Starting OSINT Platform VPS Setup with Tor & PostgreSQL...")

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    # Setup Tor
    if not setup_tor():
        logging.warning("Tor setup failed, but continuing with setup...")

    # Setup PostgreSQL
    if not setup_postgresql():
        logging.warning("PostgreSQL setup failed, but continuing with setup...")

    # Setup NLTK data
    if not setup_nltk_data():
        sys.exit(1)

    logging.info("🎉 VPS setup completed successfully!")
    logging.info("You can now start the OSINT platform with:")
    logging.info("gunicorn --bind 0.0.0.0:5000 --workers 2 main:app")
    logging.info("")
    logging.info("Service management:")
    logging.info("- Check status: sudo systemctl status osint-bots")
    logging.info("- View logs: sudo journalctl -u osint-bots -f")
    logging.info("- Restart: sudo systemctl restart osint-bots")
    logging.info("- Tor status: sudo systemctl status tor")
    logging.info("- Database: postgresql://osint_user:secure_password_2024@localhost:5432/osint_db")

if __name__ == "__main__":
    main()
