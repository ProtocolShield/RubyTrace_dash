import nltk
import os
from config import NLTK_DATA_PATH

def download_nltk_data():
    os.makedirs(NLTK_DATA_PATH, exist_ok=True)
    nltk.data.path.append(NLTK_DATA_PATH)
    print("Downloading NLTK stopwords...")
    nltk.download('stopwords', download_dir=NLTK_DATA_PATH)
    print("Downloading NLTK punkt...")
    nltk.download('punkt', download_dir=NLTK_DATA_PATH)
    print("Downloading NLTK averaged_perceptron_tagger...")
    nltk.download('averaged_perceptron_tagger', download_dir=NLTK_DATA_PATH)
    print("Downloading NLTK wordnet...")
    nltk.download('wordnet', download_dir=NLTK_DATA_PATH)
    print("NLTK data download complete.")

if __name__ == "__main__":
    download_nltk_data()
