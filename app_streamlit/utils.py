import streamlit as st
import sys
import os
from dotenv import load_dotenv


def initialize_workspace():
    """
    Initialize scholarship workspace path and add Scholarship NLP functions to Python path.
    This ensures consistent access to data and utilities across all pages in the Scholarship Intelligence Platform.
    """

    # Load environment variables from .env file (e.g., API keys, DB configs)
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

    def get_base_dir():
        """
        Resolve the base directory depending on whether we're inside 'pages' or root.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(current_dir) == 'pages':
            return os.path.dirname(current_dir)
        else:
            return current_dir

    base_dir = get_base_dir()

    # Detect environment and set appropriate workspace path
    if "/usr/src/app" in __file__:
        # Running inside Docker/container
        workspace_path = "../workspace"
        # Mounted workspace directory for scholarship functions
    else:
        # Running locally
        workspace_path = os.path.join(base_dir, "..", "workspace")

    # Ensure workspace path exists and add to Python path
    if os.path.exists(workspace_path):
        sys.path.append(workspace_path)
    else:
        workspace_path = None

    # Store workspace path in Streamlit session state for global access
    st.session_state.workspace_path = workspace_path