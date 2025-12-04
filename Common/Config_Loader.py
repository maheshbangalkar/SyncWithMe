import os
import json
import configparser
from dotenv import load_dotenv
from google import genai
from Common.Logger_Config import logging
import streamlit as st


class Config:
    def __init__(self, config_path=None):

        # Detect if running on Streamlit Cloud
        self.is_streamlit_cloud = "STREAMLIT_SERVER_ENABLED" in os.environ

        if self.is_streamlit_cloud:
            logging.info("Running on Streamlit Cloud → Using st.secrets")
            self._load_streamlit_secrets()
        else:
            logging.info("Running Locally → Using Secrets folder")
            self._load_local_secrets(config_path)

    # ------------------------------------------------------------
    # LOAD SECRETS FROM STREAMLIT CLOUD
    # ------------------------------------------------------------
    def _load_streamlit_secrets(self):

        # API Key
        if "GEMINI_API_KEY" not in st.secrets:
            raise KeyError("GEMINI_API_KEY missing in Streamlit Secrets")

        self.api_key = st.secrets["GEMINI_API_KEY"]

        # Config.ini sections (already converted to TOML)
        self.config = {
            "API": {},
            "MODEL": dict(st.secrets.get("MODEL", {})),
            "SHEET": dict(st.secrets.get("SHEET", {}))
        }

        # Google Service Account JSON (TOML → dict)
        self.google_creds = st.secrets.get("google_service_account", None)

    # ------------------------------------------------------------
    # LOAD LOCAL FILES FROM Secrets/
    # ------------------------------------------------------------
    def _load_local_secrets(self, config_path):

        # Base directories
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        SECRETS_DIR = os.path.join(BASE_DIR, "Secrets")

        # Validate Secrets folder
        if not os.path.exists(SECRETS_DIR):
            raise FileNotFoundError(f"Secrets folder missing at: {SECRETS_DIR}")

        # Load .env
        env_path = os.path.join(SECRETS_DIR, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            raise FileNotFoundError(f".env file missing at: {env_path}")

        # Load Config.ini
        if config_path is None:
            config_path = os.path.join(SECRETS_DIR, "Config.ini")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config.ini file missing at: {config_path}")

        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        # Load API key
        self.api_key = os.getenv("API_KEY") or self.config["API"].get("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY missing in .env or Config.ini")

        # Load Google Service Account JSON
        sa_path = os.path.join(SECRETS_DIR, "Service_Account.json")
        if os.path.exists(sa_path):
            with open(sa_path, "r") as f:
                self.google_creds = json.load(f)
        else:
            self.google_creds = None

    # ------------------------------------------------------------
    # Create Gemini Client
    # ------------------------------------------------------------
    def get_client(self):
        try:
            return genai.Client(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini client: {e}")

    # ------------------------------------------------------------
    # Fetch Model Name
    # ------------------------------------------------------------
    def get_model(self, model_name):
        model_section = {}

        if self.is_streamlit_cloud:
            model_section = self.config.get("MODEL", {})
        else:
            model_section = self.config["MODEL"]

        if model_name in model_section:
            return model_section[model_name]

        raise ValueError(f"Model not found: {model_name}")

    # ------------------------------------------------------------
    # Load System Instruction
    # ------------------------------------------------------------
    def get_system_instruction(self):
        try:
            if self.is_streamlit_cloud:
                # Cloud → load from st.secrets
                return st.secrets.get("SYSTEM_INSTRUCTION", None)

            # Local → read file
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            SECRETS_DIR = os.path.join(BASE_DIR, "Secrets")
            sys_file = os.path.join(SECRETS_DIR, "SYSTEM_INSTRUCTION.txt")

            if not os.path.exists(sys_file):
                logging.warning(f"SYSTEM_INSTRUCTION.txt not found at: {sys_file}")
                return None

            with open(sys_file, "r", encoding="utf-8") as f:
                return f.read().strip()

        except Exception as e:
            logging.error(f"Error loading system instruction: {e}")
            return None

    # ------------------------------------------------------------
    # Fetch Sheet Value
    # ------------------------------------------------------------
    def fetch_sheet_value(self, key):
        if self.is_streamlit_cloud:
            return self.config["SHEET"].get(key)
        return self.config["SHEET"][key]

    # ------------------------------------------------------------
    # Fetch Any Key
    # ------------------------------------------------------------
    def fetch_key_value(self, key_name):
        if self.is_streamlit_cloud:
            for section in self.config.values():
                if key_name in section:
                    return section[key_name]
        else:
            for section in self.config.sections():
                if key_name in self.config[section]:
                    return self.config[section][key_name]
        raise KeyError(f"Key '{key_name}' not found")


# GLOBAL CONFIG OBJECT
config = Config()
