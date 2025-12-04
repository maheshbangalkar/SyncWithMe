from google.genai import types
from Common.Logger_Config import logging
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
        self.sheet_data = sheet      # Instance of SheetClass OR None
        self.session_history = []    # Stores conversation context

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

        try:
            # PRO models FORCE thinking mode
            if c.PRO_MODEL in self.model or thinking_mode is True:
                thinking_config = types.ThinkingConfig(
                    include_thoughts=True,
                    thinking_budget=c.MODEL_THINKING_BUDGET
                )
                is_think = True
            else:
                thinking_config = None
        except Exception as e:
            logging.warning(f"Error configuring thinking mode: {e}")
            thinking_config = None

        # -------------------------------------------------------------
        # SYSTEM INSTRUCTION (from Secrets folder or Streamlit Secrets)
        # -------------------------------------------------------------
        try:
            sys_ins = config.get_system_instruction()
            logging.info(f"SYSTEM INSTRUCTION : {sys_ins}")
        except Exception as e:
            logging.warning(f"Error loading system instruction: {e}")
            sys_ins = None

        # -------------------------------------------------------------
        # UPDATE CONTEXT HISTORY
        # -------------------------------------------------------------
        self.session_history.append({"user": question, "assistant": ""})
        context_history = self.session_history[-c.MAX_CONTEXT:]

        # Build context string for LLM
        try:
            context_text = common.build_context_text(context_history)
        except Exception as e:
            logging.error(f"Error building context: {e}")
            context_text = question

        # -------------------------------------------------------------
        # CALL GOOGLE GENAI (new API format)
        # -------------------------------------------------------------
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=context_text,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=c.MAX_OUTPUT_TOKEN_LENGTH,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    thinking_config=thinking_config,
                    system_instruction=types.Content(
                        role="system",
                        parts=[types.Part(text=sys_ins or "")]
                    ),
                )
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

        # -------------------------------------------------------------
        # EXTRACT TEXT RESPONSE
        # -------------------------------------------------------------
        try:
            bot_text = ""

            # Primary modern API: response.text
            if hasattr(response, "text") and response.text:
                bot_text = response.text.strip()

            # Fallback: candidates/parts API
            elif hasattr(response, "candidates") and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        bot_text += part.text
                bot_text = bot_text.strip()

            else:
                bot_text = "I'm sorry, I couldn't generate a proper response."

            # Save assistant response into session history
            self.session_history[-1]["assistant"] = bot_text

            # Format pretty response text (removes raw JSON parts)
            formatted_response = common.format_template(
                c.FORMATTED_RESPONSE_TEMPLATE,
                {"question": question, "answer": bot_text}
            )

            # Usage stats extraction
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

            # ---------------------------------------------------------
            # SAVE TO GOOGLE SHEET (instance method, not static)
            # ---------------------------------------------------------
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
        """Standalone terminal chatbot."""
        print(f"Welcome to SyncWithMeChatBot! Using model: {self.model}")
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
