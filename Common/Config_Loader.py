import os
import json
import configparser
from dotenv import load_dotenv
from google.genai.client import Client
from Common.Logger_Config import logging
import streamlit as st


class Config:
    def __init__(self, config_path=None):

        self.is_streamlit_cloud = False
        try:
            if hasattr(st, "secrets") and len(st.secrets) > 0:
                self.is_streamlit_cloud = True
        except:
            self.is_streamlit_cloud = False

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

        # Required API Key
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        if not self.api_key:
            raise KeyError("❌ GEMINI_API_KEY missing in Streamlit Secrets")

        # Load MODEL and SHEET sections
        self.config = {
            "MODEL": dict(st.secrets.get("MODEL", {})),
            "SHEET": dict(st.secrets.get("SHEET", {}))
        }

        # Load Service Account JSON
        self.google_creds = st.secrets.get("google_service_account")

        self.system_instruction_table = (
            st.secrets.get("SYSTEM_INSTRUCTION_FILE")
            or st.secrets.get("system_instruction_file")
            or None
        )

        if self.system_instruction_table:
            logging.info("✅ SYSTEM_INSTRUCTION_FILE loaded successfully from Streamlit Secrets.")
        else:
            logging.warning("❌ SYSTEM_INSTRUCTION_FILE missing in Streamlit Secrets.")

    # ------------------------------------------------------------
    # LOAD LOCAL FILES FROM Secrets/
    # ------------------------------------------------------------
    def _load_local_secrets(self, config_path):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        SECRETS_DIR = os.path.join(BASE_DIR, "Secrets")

        # Validate Secrets folder
        if not os.path.exists(SECRETS_DIR):
            raise FileNotFoundError(f"❌ Secrets folder missing at: {SECRETS_DIR}")

        # Load .env
        env_path = os.path.join(SECRETS_DIR, ".env")
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"❌ .env missing at: {env_path}")
        load_dotenv(env_path)

        # Load Config.ini
        if config_path is None:
            config_path = os.path.join(SECRETS_DIR, "Config.ini")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"❌ Config.ini missing at: {config_path}")

        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        # API Key
        self.api_key = (
            os.getenv("GEMINI_API_KEY")
            or self.config["API"].get("GEMINI_API_KEY")
        )
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY missing in .env or Config.ini")

        # Service Account JSON
        sa_path = os.path.join(SECRETS_DIR, "Service_Account.json")
        self.google_creds = (
            json.load(open(sa_path)) if os.path.exists(sa_path) else None
        )

    # ------------------------------------------------------------
    # Gemini Client
    # ------------------------------------------------------------
    def get_client(self):
        try:
            return Client(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to initialize Gemini client: {e}")

    # ------------------------------------------------------------
    # Model Name Fetch
    # ------------------------------------------------------------
    def get_model(self, model_name):

        section = (
            self.config.get("MODEL", {})
            if self.is_streamlit_cloud
            else self.config["MODEL"]
        )

        if model_name not in section:
            raise ValueError(f"❌ Model not found: {model_name}")

        return section[model_name]

    # ------------------------------------------------------------
    # System Instruction Loader
    # ------------------------------------------------------------
    def get_system_instruction(self):
        try:
            if self.is_streamlit_cloud:

                table = (
                    self.system_instruction_table
                    or st.secrets.get("SYSTEM_INSTRUCTION_FILE")
                    or st.secrets.get("system_instruction_file")
                )

                if table:
                    inst = table.get("SYSTEM_INSTRUCTION")
                    if inst:
                        logging.info("✅ SYSTEM_INSTRUCTION loaded from Streamlit")
                        return inst.strip()

                logging.warning("❌ SYSTEM_INSTRUCTION not found in Streamlit secrets.")
                return None

            # Local machine
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(BASE_DIR, "Secrets", "SYSTEM_INSTRUCTION.txt")

            if os.path.exists(file_path):
                return open(file_path, "r", encoding="utf-8").read().strip()

            logging.warning(f"⚠ SYSTEM_INSTRUCTION.txt not found at: {file_path}")
            return None

        except Exception as e:
            logging.error(f"❌ Error loading system instruction: {e}")
            return None

    # ------------------------------------------------------------
    # Sheet Values Fetch
    # ------------------------------------------------------------
    def fetch_sheet_value(self, key):
        return self.config["SHEET"].get(key)

    # ------------------------------------------------------------
    # General Key Finder
    # ------------------------------------------------------------
    def fetch_key_value(self, key_name):
        # Streamlit CLOUD MODE
        if self.is_streamlit_cloud:
            if key_name in st.secrets:
                return st.secrets[key_name]

            for section_name, section in self.config.items():
                if isinstance(section, dict) and key_name in section:
                    return section[key_name]
            for section_name, section in st.secrets.items():
                if isinstance(section, dict) and key_name in section:
                    return section[key_name]

        # LOCAL MODE
        else:

            for sec in self.config.sections():
                if key_name in self.config[sec]:
                    return self.config[sec][key_name]
            env_value = os.getenv(key_name)
            if env_value:
                return env_value
        raise KeyError(f"❌ Key '{key_name}' not found in any config source.")

# GLOBAL SINGLETON
config = Config()
