import os
import gspread
from google.oauth2.service_account import Credentials
from Common.Config_Loader import config
from Common.Logger_Config import logging
from datetime import datetime
from gspread_formatting import (
    Border,
    Borders,
    CellFormat,
    format_cell_range
)
from Common import Constant as c

CURRENT_FILE = os.path.abspath(__file__)
APP_DIR = os.path.dirname(os.path.dirname(CURRENT_FILE))   
BASE_DIR = os.path.dirname(APP_DIR)                       
SECRETS_DIR = os.path.join(BASE_DIR, "secrets")


class SheetClass:
    def __init__(self):
        """
        Initializes Google Sheet Manager using configuration values.
        """
        # Only filename comes from config. Path is resolved here.
        service_file_name = config.fetch_sheet_value("SERVICE_ACCOUNT_FILE").strip()

        # Correct absolute path:
        self.service_account_file = os.path.join(SECRETS_DIR, service_file_name)

        self.spreadsheet_id = config.fetch_sheet_value("SPREADSHEET_ID").strip()
        self.sheet_name = config.fetch_sheet_value("SHEET_NAME").strip()
        self.scopes = [s.strip() for s in config.fetch_sheet_value("SCOPES").split(",")]

        self.sheet = None

        self.get_sheet()


    def get_sheet(self):
        """
        Authenticates the Google Sheet and loads the worksheet.
        """
        try:
            if not os.path.exists(self.service_account_file):
                raise FileNotFoundError(
                    f"Service account file not found: {self.service_account_file}"
                )

            credentials = Credentials.from_service_account_file(
                self.service_account_file,
                scopes=self.scopes
            )

            client = gspread.authorize(credentials)
            self.sheet = client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)

            logging.info(f"Successfully accessed sheet: {self.sheet_name}")

        except FileNotFoundError as fnf:
            logging.error(fnf)
            raise

        except gspread.SpreadsheetNotFound:
            logging.error(f"Spreadsheet with ID '{self.spreadsheet_id}' not found or access denied.")
            raise

        except Exception as e:
            logging.error(f"Error accessing the Google Sheet: {e}")
            raise


    def _convert_to_column_letter(self, col):
        letters = ""
        while col:
            col, remainder = divmod(col - 1, 26)
            letters = chr(65 + remainder) + letters
        return letters


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


    def get_next_sr_no(self):
        try:
            values = self.sheet.col_values(1)
            if len(values) <= 1:
                return 1
            return int(values[-1]) + 1
        except Exception as e:
            logging.error(f"Error getting serial number: {e}")
            return 1


    def save_question_response(self, question, is_think, model_used,
                               response=c.NA, bot_text=c.NA,
                               formatted_response=None, formatted_usage=None):

        try:
            sr_no = self.get_next_sr_no()
            datestamp = datetime.now().strftime(c.DATE_FORMAT)

            status = c.RECEIVED if (response and not isinstance(response, str)) else c.FAILED

            if isinstance(response, str) or isinstance(response, Exception) or (c.ERROR.lower() in response):
                bot_text_safe = response
                formatted_safe = c.NO_RESPONSE
                status = c.FAILED
            else:
                bot_text_safe = bot_text if bot_text else (response if response else c.EMPTY_ANSWER)
                formatted_safe = formatted_response if formatted_response else (response if response else c.NO_RESPONSE)
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
