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

        # Reliable Cloud Detection
        self.is_streamlit_cloud = os.getenv("STREAMLIT_RUNTIME_ENVIRONMENT") == "cloud"

        # Load Sheet Settings
        self.spreadsheet_id = config.fetch_sheet_value("SPREADSHEET_ID")
        self.sheet_name = config.fetch_sheet_value("SHEET_NAME")

        raw_scopes = config.fetch_sheet_value("SCOPES")
        self.scopes = raw_scopes if isinstance(raw_scopes, list) else [
            s.strip() for s in raw_scopes.split(",")
        ]

        self.sheet = None
        self._authenticate_and_load_sheet()

    # -------------------------------------------------------
    # Authentication + Sheet Load
    # -------------------------------------------------------
    def _authenticate_and_load_sheet(self):
        try:
            if self.is_streamlit_cloud:
                logging.info("Using Streamlit Cloud Google credentials")

                service_info = st.secrets.get("google_service_account")
                if not service_info:
                    raise ValueError("❌ google_service_account missing in Streamlit Secrets")

                credentials = Credentials.from_service_account_info(
                    service_info, scopes=self.scopes
                )

            else:
                logging.info("Using Local Google JSON credentials")

                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                SECRETS_DIR = os.path.join(BASE_DIR, "Secrets")

                service_file = os.path.join(
                    SECRETS_DIR,
                    config.fetch_sheet_value("SERVICE_ACCOUNT_FILE")
                )

                if not os.path.exists(service_file):
                    raise FileNotFoundError(f"❌ Service Account JSON missing at: {service_file}")

                credentials = Credentials.from_service_account_file(
                    service_file, scopes=self.scopes
                )

            # Connect to Google Sheets
            client = gspread.authorize(credentials)
            self.sheet = client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)

            logging.info(f"✅ Google Sheet Loaded: {self.sheet_name}")

        except Exception as e:
            logging.error(f"❌ Error loading Google Sheet: {e}")
            raise

    # -------------------------------------------------------
    # Column Number → Letter
    # -------------------------------------------------------
    def _convert_to_column_letter(self, col):
        letters = ""
        while col:
            col, remainder = divmod(col - 1, 26)
            letters = chr(65 + remainder) + letters
        return letters

    # -------------------------------------------------------
    # Add Border Formatting
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
            logging.error(f"❌ Border Formatting Error: {e}")

    # -------------------------------------------------------
    # Get Next Serial No.
    # -------------------------------------------------------
    def get_next_sr_no(self):
        try:
            values = self.sheet.col_values(1)
            if len(values) <= 1:
                return 1
            return int(values[-1]) + 1
        except:
            return 1

    # -------------------------------------------------------
    # Save Entry
    # -------------------------------------------------------
    def save_question_response(
        self, question, is_think, model_used,
        response=c.NA, bot_text=c.NA,
        formatted_response=None, formatted_usage=None):

        try:
            sr_no = self.get_next_sr_no()
            datestamp = datetime.now().strftime(c.DATE_FORMAT)

            # Determine status
            if isinstance(response, str) or isinstance(response, Exception):
                status = c.FAILED
                bot_text_safe = str(response)
                formatted_safe = c.NO_RESPONSE
            else:
                status = c.RECEIVED
                bot_text_safe = bot_text or response
                formatted_safe = formatted_response or response

            row_data = [
                sr_no, question, is_think,
                model_used, bot_text_safe,
                status, datestamp,
                formatted_safe, formatted_usage
            ]

            self.sheet.append_row(row_data)

            new_row_index = len(self.sheet.get_all_values())
            self.add_all_borders_to_row(new_row_index)

            logging.info("✅ Row saved successfully")

        except Exception as e:
            logging.error(f"❌ Failed to append row: {e}")
