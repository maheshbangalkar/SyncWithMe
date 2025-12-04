from google import genai
from Common.Config_Loader import config
from Common.Sheet_Functions import SheetClass as sc
from .SyncWithMeChatBot import SyncWithMeChatBot

if __name__ == "__main__":
    sheet = sc()
    client = config.get_client()
    gemini_model = config.get_model("GEMINI_2_5_FLASH")
    chatbot = SyncWithMeChatBot(client, gemini_model, sheet)
    chatbot.run_chatbot()