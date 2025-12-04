from google.genai import types
from Common.Logger_Config import logging
from Common.Common_Functions import CommonFunctions as common
from Common.Sheet_Functions import SheetClass as sc
from Common import Constant as c
import json

class SyncWithMeChatBot:
    def __init__(self, client, model, sheet_data):
        """
        Initializes the chatbot with the required client, model, and Google Sheet.
        """
        self.client = client
        self.model = model
        self.session_history = []
        self.sheet_data = sheet_data
    
    def get_gemini_text_response(self, question, user_input = False):
        """
        Sends a question to the model and returns the chatbot's response.
        Saves logs (Responses) to Google Sheet with robust error handling.
        """
        is_think = False
        thinking_config = None
        try:
            if c.PRO_MODEL in self.model:
                thinking_config = types.ThinkingConfig(thinking_budget=c.MODEL_THINKING_BUDGET)
                is_think = True
            else:
                # user_input = input("Would you like the model to use reasoning before responding? (y/n): ").strip().lower()
                if user_input == True:
                    # Enable thinking
                    thinking_config = types.ThinkingConfig(include_thoughts=True, thinking_budget=c.MODEL_THINKING_BUDGET)
                    is_think = True
                else:
                    # Disable thinking
                    thinking_config = None
        except Exception as e:
            logging.warning(f"Error reading user input: {e}")
            thinking_config = None

        try:
            sys_ins = c.SYSTEM_INSTRUCTION if True else None
        except Exception as e:
            logging.warning(f"Error setting system instruction: {e}")
            sys_ins = None

        self.session_history.append({"user": question, "assistant": ""})
        context_history = self.session_history[-c.MAX_CONTEXT:] 

        try:
            context_text = common.build_context_text(context_history)
            print(f"Context Message: {context_text}")
        except Exception as e:
            logging.error(f"Error building context: {e}")
            context_text = question

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=context_text,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=c.MAX_OUTPUT_TOKEN_LENGTH,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    # safety_settings=[
                    #     types.SafetySetting(
                    #         category=c.HARM_CATEGORY_HARASSMENT,
                    #         threshold=c.BLOCK_ONLY_HIGH
                    #     ),
                    #     types.SafetySetting(
                    #         category=c.HARM_CATEGORY_HATE_SPEECH,
                    #         threshold=c.BLOCK_ONLY_HIGH
                    #     ),
                    #     types.SafetySetting(
                    #         category=c.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    #         threshold=c.BLOCK_ONLY_HIGH
                    #     ),
                    #     types.SafetySetting(
                    #         category=c.HARM_CATEGORY_DANGEROUS_CONTENT,
                    #         threshold=c.BLOCK_ONLY_HIGH
                    #     ),
                    # ],
                    thinking_config=thinking_config,
                    system_instruction=sys_ins,
                )
            )
            print(f"thinking_config: {thinking_config}")
        except Exception as api_error:
            logging.error(f"Error calling generate_content API: {api_error}", exc_info=True)
            try:
                sc.save_question_response(
                    self.sheet_data, question, is_think, self.model,
                    str(api_error), c.NO_RESPONSE, c.ERROR, c.NA
                )
            except Exception as sheet_error:
                logging.error(f"Error saving API error to Google Sheet: {sheet_error}")
            print("Sorry, there was an error communicating with the model.")
            return None

        try:
            bot_text = ""

            if hasattr(response, "text") and response.text:
                bot_text = response.text.strip()

            elif hasattr(response, "candidates") and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        bot_text += part.text
                bot_text = bot_text.strip()

            else:
                bot_text = "I'm sorry, but I couldn't generate a proper response."

            self.session_history[-1]["assistant"] = bot_text
            
            # sources = common.extract_sources(response)
            
            formatted_response = common.format_template(
                c.FORMATTED_RESPONSE_TEMPLATE,
                # {"question": question, "answer": bot_text, "sources": sources}
                {"question": question, "answer": bot_text}
            )

            print(f"SyncWithMe ChatBot: {bot_text}")

            # print(f"Full Response:{common.sdk_dump_to_json(response)}")
            # print(f"Sources: {common.extract_sources(response)}")

            usage = response.usage_metadata
            formatted_usage = common.format_template(
                c.FORMATTED_RESPONSE_USAGE_TEMPLATE,
                {
                    "prompt_token": usage.prompt_token_count,
                    "output_token": usage.candidates_token_count,
                    "thinking_token": usage.thoughts_token_count,
                    "total_token": usage.total_token_count
                }
            )
            print(f"Usage: {formatted_usage}")

            try:
                sc.save_question_response(
                    self.sheet_data, question, is_think, self.model,
                    response, bot_text, formatted_response, formatted_usage
                )
            except Exception as sheet_error:
                logging.error(f"Error saving to Google Sheet: {sheet_error}")

            # return formatted_response
            return bot_text

        except Exception as e:
            logging.error(f"Error processing model response: {e}", exc_info=True)
            print("Sorry, something went wrong with processing the chatbot response.")
            return None

    def run_chatbot(self):
        """Interactive chat with optional image upload or default test image."""
        print(f"Welcome to SyncWithMeChatBot! Using model: {self.model}")

        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "q", "x"]:
                print("Exiting SyncWithMeChatBot. Goodbye!")
                break
            self.get_gemini_text_response(user_input)

    def get_history(self):
        """
        Returns the full conversation history.
        """
        return self.session_history

    def clear_history(self):
        """
        Clears the conversation history.
        """
        self.session_history = []
