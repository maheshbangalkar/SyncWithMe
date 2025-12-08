
import streamlit as st
from Common.Logger_Config import logging

from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
    Content,
    Part,
)

from Common.Common_Functions import CommonFunctions as common
from Common import Constant as c
from Common.Config_Loader import config
import json

class SyncWithMeChatBot:
    def __init__(self, client, model, sheet):
        """
        Initializes the chatbot with client, model, and Google Sheet instance.
        """
        self.client = client
        self.model = model
        self.sheet_data = sheet
        self.session_history = []

    # =====================================================================
    # Generate Chatbot Response
    # =====================================================================
    def get_gemini_text_response(self, question, thinking_mode=False):
        """
        Sends a question to Gemini model and returns the chatbot response.
        Saves response logs to Google Sheets when available.
        """

        # -------------------------------------------------------------
        # THINKING MODE CONFIG
        # -------------------------------------------------------------
        is_think = False
        thinking_config = None

        if (c.PRO_MODEL in self.model.lower()) or thinking_mode:
            is_think = True
            thinking_config = {
                "include_thoughts": True,
                "thinking_budget": c.MODEL_THINKING_BUDGET,
            }

        # SYSTEM INSTRUCTION
        try:
            sys_ins = config.get_system_instruction() or ""
        except Exception as e:
            logging.warning(f"Error loading system instruction: {e}")
            sys_ins = None

        # -------------------------------------------------------------
        # BUILD CONTEXT HISTORY
        # -------------------------------------------------------------
        self.session_history.append({"user": question, "assistant": ""})
        context_text = common.build_context_text(
            self.session_history[-c.MAX_CONTEXT:]
        )

        # -------------------------------------------------------------
        # GOOGLE SEARCH TOOL
        # -------------------------------------------------------------
        tools = [Tool(google_search=GoogleSearch())]

        # API CALL
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=context_text,
                config=GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=c.MAX_OUTPUT_TOKEN_LENGTH,
                    tools=tools,
                    thinking_config=thinking_config,
                    system_instruction=Content(
                        role="system",
                        parts=[Part(text=sys_ins)],
                    ),
                ),
            )
        except Exception as api_error:
            logging.error(f"Error calling generate_content API: {api_error}", exc_info=True)

            # Log failure to Google Sheet if possible
            if self.sheet_data:
                try:
                    self.sheet_data.save_question_response(
                        question, is_think, self.model,
                        str(api_error), c.NO_RESPONSE, c.ERROR, c.NA
                    )
                except Exception as sheet_error:
                    logging.error(f"Error saving API error to Google Sheet: {sheet_error}")

            return "Sorry, there was an error communicating with the model."

        # EXTRACT TEXT
        try:
            bot_text = ""

            # Primary modern API: response.text
            if hasattr(response, "text") and response.text:
                bot_text = response.text.strip()

            # Fallback: candidates/parts API
            elif hasattr(response, "candidates") and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text"):
                        bot_text += part.text
                bot_text = bot_text.strip()

            else:
                bot_text = "I'm sorry, I couldn't generate a proper response."

            self.session_history[-1]["assistant"] = bot_text

            # Format output
            formatted_response = common.format_template(
                c.FORMATTED_RESPONSE_TEMPLATE,
                {"question": question, "answer": bot_text}
            )

            # Usage stats
            usage = response.usage_metadata
            formatted_usage = common.format_template(
                c.FORMATTED_RESPONSE_USAGE_TEMPLATE,
                {
                    "prompt_token": usage.prompt_token_count,
                    "output_token": usage.candidates_token_count,
                    "thinking_token": getattr(usage, "thoughts_token_count", 0),
                    "total_token": usage.total_token_count,
                }
            )

            # Save logs to Google Sheet
            if self.sheet_data:
                try:
                    self.sheet_data.save_question_response(
                        question, is_think, self.model,
                        response, bot_text,
                        formatted_response, formatted_usage
                    )
                except Exception as sheet_error:
                    logging.error(f"Error saving to Google Sheet: {sheet_error}")

            return bot_text or "I'm sorry, I couldn't generate a response."

        except Exception as e:
            logging.error(f"Error processing model response: {e}", exc_info=True)
            return "Sorry, something went wrong while processing the response."

    # =====================================================================
    # UTILITY FUNCTIONS
    # =====================================================================
    def run_chatbot(self):
        print(f"Welcome to SyncWithMe ChatBot! Using model: {self.model}")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "q", "x"]:
                break
            print("Bot:", self.get_gemini_text_response(user_input))

    def get_history(self):
        """Returns conversation history."""
        return self.session_history

    def clear_history(self):
        """Clears conversation history."""
        self.session_history = []
