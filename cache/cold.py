"""Module to set up all data and resources to cold start the application."""

#standard
import os

#third-party
import nltk
from dotenv import load_dotenv

#internal
from .core import (
    connect_database,
    load_cross_encoder,
    load_react_prompt_template,
    load_search_engine,
    load_summary_prompt_template,
    load_vector_database,
)
from common import streamlit_cache

@streamlit_cache("Downloading corpora for stopwords", "data")
def download_stopwords() -> None:
    """Download nltk corpora for stopwords and set the directory to store it."""
    path = os.getenv("NLTK_DATA", "/usr/share/nltk_data")
    nltk.download("stopwords", download_dir=path, quiet=True)

@streamlit_cache("Setting up application dependencies", "data")
def cold_start() -> None:
    """Execute cold start setup before running application, including environment variables.
    
    The process would take to execute various functionalities within the system that does not
    require any runtime state. It's preferable to take precedence to load in order to perceive good 
    user experience.

    """
    load_dotenv()
    connect_database()
    download_stopwords()
    load_cross_encoder()
    load_react_prompt_template()
    load_search_engine()
    load_summary_prompt_template()
    load_vector_database()
