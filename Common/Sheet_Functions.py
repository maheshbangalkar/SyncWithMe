import os
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from datetime import datetime
from gspread_formatting import Border, Borders, CellFormat, format_cell_range

from Common.Config_Loader import config
from Common.Logger_Config import logging
from Common import Constant as c


class SheetClass:
    def __init__(self):
        """
        Initializes Google Sheet Manager.
        Automatically detects:
        - Local environment → use Secrets folder files
        - Streamlit Cloud → use st.secrets
        """

        self.is_streamlit_cloud = os.getenv("STREAMLIT_DEPLOYMENT") == "cloud"

        # Load sheet config from Config Loader
        self.spreadsheet_id = config.fetch_sheet_value("SPREADSHEET_ID")
        self.sheet_name = config.fetch_sheet_value("SHEET_NAME")

        raw_scopes = config.fetch_sheet_value("SCOPES")

        # Streamlit Secrets uses list for scopes, local uses comma separated
        if isinstance(raw_scopes, list):
            self.scopes = raw_scopes
        else:
            self.scopes = [s.strip() for s in raw_scopes.split(",")]

        self.sheet = None
        self._authenticate_and_load_sheet()

    # -------------------------------------------------------
    # Authenticate & Load Sheet
    # -------------------------------------------------------
    def _authenticate_and_load_sheet(self):
        try:
            if self.is_streamlit_cloud:
                logging.info("Using Streamlit Cloud credentials for Google Sheets")

                # Use Google credentials from st.secrets (already TOML formatted)
                service_info = st.secrets.get("google_service_account")
                if not service_info:
                    raise ValueError("Missing [google_service_account] in Streamlit Secrets")

                credentials = Credentials.from_service_account_info(
                    service_info,
                    scopes=self.scopes
                )

            else:
                logging.info("Using local JSON credentials from Secrets folder")

                # Fix BASE_DIR path
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                SECRETS_DIR = os.path.join(BASE_DIR, "Secrets")

                service_file_name = config.fetch_sheet_value("SERVICE_ACCOUNT_FILE")
                service_account_file = os.path.join(SECRETS_DIR, service_file_name)

                if not os.path.exists(service_account_file):
                    raise FileNotFoundError(f"Service Account file missing: {service_account_file}")

                credentials = Credentials.from_service_account_file(
                    service_account_file,
                    scopes=self.scopes
                )

            # Connect to Google Sheets
            client = gspread.authorize(credentials)
            self.sheet = client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)

            logging.info(f"Successfully accessed sheet: {self.sheet_name}")

        except Exception as e:
            logging.error(f"Error loading Google Sheet: {e}")
            raise

    # -------------------------------------------------------
    # Convert numeric col → Excel letter
    # -------------------------------------------------------
    def _convert_to_column_letter(self, col):
        letters = ""
        while col:
            col, remainder = divmod(col - 1, 26)
            letters = chr(65 + remainder) + letters
        return letters

    # -------------------------------------------------------
    # Apply borders to new row
    # -------------------------------------------------------
    def add_all_borders_to_row(self, row_number):
        try:
            row_values = self.sheet.row_values(row_number)
            last_col_index = len(row_values)
            if last_col_index == 0:
                return

            last_col_letter = self._convert_to_column_letter(last_col_index)
            b = Border(c.SOLID_BORDER)
            border_format = CellFormat(borders=Borders(top=b, bottom=b, left=b, right=b))

            range_str = f"A{row_number}:{last_col_letter}{row_number}"
            format_cell_range(self.sheet, range_str, border_format)

        except Exception as e:
            logging.error(f"Error applying ALL borders: {e}")

    # -------------------------------------------------------
    # Get next serial number
    # -------------------------------------------------------
    def get_next_sr_no(self):
        try:
            values = self.sheet.col_values(1)
            if len(values) <= 1:
                return 1
            return int(values[-1]) + 1
        except Exception as e:
            logging.error(f"Error getting serial number: {e}")
            return 1

    # -------------------------------------------------------
    # Save Question + Response to Google Sheet
    # -------------------------------------------------------
    def save_question_response(self, question, is_think, model_used,
                               response=c.NA, bot_text=c.NA,
                               formatted_response=None, formatted_usage=None):

        try:
            sr_no = self.get_next_sr_no()
            datestamp = datetime.now().strftime(c.DATE_FORMAT)

            # Determine status
            status = c.RECEIVED if (response and not isinstance(response, str)) else c.FAILED

            if isinstance(response, str) or isinstance(response, Exception) or (c.ERROR.lower() in str(response).lower()):
                bot_text_safe = str(response)
                formatted_safe = c.NO_RESPONSE
                status = c.FAILED
            else:
                bot_text_safe = bot_text if bot_text else response
                formatted_safe = formatted_response if formatted_response else response
                status = c.RECEIVED

            row_data = [
                sr_no, question, is_think, model_used,
                bot_text_safe, status, datestamp,
                formatted_safe, formatted_usage
            ]

            self.sheet.append_row(row_data)

            new_row_index = len(self.sheet.get_all_values())
            self.add_all_borders_to_row(new_row_index)

            logging.info("Data Saved Successfully")

        except Exception as e:
            logging.error(f"Failed to append row: {e}")
            print("Failed to save. Please try again later.")
