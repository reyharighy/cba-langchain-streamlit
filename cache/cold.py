"""Module to set up all dependencies data to cold start the application."""

#standard
import os

#third-party
import nltk
from dotenv import load_dotenv

#internal
from .core import load_sentence_transformer
from common import streamlit_cache

@streamlit_cache("Downloading corpora for stopwords", "data")
def download_stopwords() -> None:
    """Download nltk corpora for stopwords and set the directory to store it."""
    path = os.getenv("NLTK_DATA", "/usr/share/nltk_data")
    nltk.download("stopwords", download_dir=path, quiet=True)

@streamlit_cache("Setting up application dependencies", "data")
def cold_start() -> None:
    """Execute cold start setup before running application, including environment variables.
    
    The process would take to execute:
    1. download_stopwords()
    2. load_sentence_transformer()

    The above processes take time too long at the first execution of user's request.
    Therefore, they take precedence in order to perceive good user experience.

    """
    load_dotenv()
    download_stopwords()
    load_sentence_transformer()
