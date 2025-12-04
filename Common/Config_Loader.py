import configparser
import os
from dotenv import load_dotenv
from google import genai
from Common.Logger_Config import logging

class Config:
    def __init__(self, config_path=None):

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        SECRETS_DIR = os.path.join(BASE_DIR, "Secrets")

        if not os.path.exists(SECRETS_DIR):
            raise FileNotFoundError(f"Secrets folder missing at: {SECRETS_DIR}")

        # ---------------------------------------
        # Load .env
        # ---------------------------------------
        env_path = os.path.join(SECRETS_DIR, ".env")

        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            raise FileNotFoundError(f".env file missing at: {env_path}")

        # ---------------------------------------
        # Load Config.ini
        # ---------------------------------------
        if config_path is None:
            config_path = os.path.join(SECRETS_DIR, "Config.ini")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config.ini file missing at: {config_path}")

        self.config = configparser.ConfigParser()
        self.config.read(config_path)


        # ---------------------------------------
        # API Key (from .env or Config.ini)
        # ---------------------------------------
        self.api_key = os.getenv("API_KEY") or self.config["API"].get("API_KEY")

        if not self.api_key:
            raise ValueError("API_KEY not found in .env or Config.ini")

        # ---------------------------------------
        # Create Google GenAI Client
        # ---------------------------------------
        self.client = self.get_client()

    # -------------------------------------------------------
    # Initialize Google GenAI Client
    # -------------------------------------------------------
    def get_client(self):
        try:
            return genai.Client(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini client: {e}")

    # -------------------------------------------------------
    # Fetch Model Name
    # -------------------------------------------------------
    def get_model(self, model_name):
        if "MODEL" not in self.config:
            raise KeyError("MODEL section missing in Config.ini")

        model_section = self.config["MODEL"]  # FIXED LINE

        # If key exists
        if model_name in model_section:
            return model_section[model_name]

        # If searching by value
        for key, value in model_section.items():
            if value == model_name:
                return value

        raise ValueError(f"Model not found: {model_name}")

    def get_system_instruction(self):
        """
        Loads system instruction text from Secrets/SYSTEM_INSTRUCTION.txt
        """
        try:
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


    # -------------------------------------------------------
    # Fetch sheet values
    # -------------------------------------------------------
    def fetch_sheet_value(self, key):
        try:
            return self.config["SHEET"][key]
        except KeyError:
            raise KeyError(f"SHEET key '{key}' not found")

    # -------------------------------------------------------
    # Fetch any key from any section
    # -------------------------------------------------------
    def fetch_key_value(self, key_name):
        for section in self.config.sections():
            if key_name in self.config[section]:
                return self.config[section][key_name]
        raise KeyError(f"Key '{key_name}' not found in any section")

# Global config object
config = Config()
