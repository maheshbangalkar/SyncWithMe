import json
import google.generativeai as genai
from Common.Config_Loader import config
import re
from enum import Enum

class CommonFunctions:
    def __init__(self):
        None
    
    def make_serializable(self, obj):
        """
        Recursively convert objects to JSON-serializable format.
        Non-serializable objects are converted to strings.
        """
        if isinstance(obj, dict):
            return {k: self.make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.make_serializable(v) for v in obj]
        elif hasattr(obj, "__dict__"):
            return self.make_serializable(vars(obj))
        else:
            try:
                json.dumps(obj)
                return obj
            except (TypeError, OverflowError):
                return str(obj)
    
    def format_template(template, updates: dict):
        """
        Copies a template, updates the first dictionary with provided values, 
        and returns the JSON string.
        """
        formatted = template.copy()
        if formatted and isinstance(formatted[0], dict):
            formatted[0].update(updates)
        return json.dumps(formatted)

    def build_context_text(context_history):
        """
        Build a formatted text transcript from a list of message dictionaries.

        Each item in `context_history` is expected to be a dictionary that may
        contain "user" and/or "assistant" keys. The function extracts these values and
        constructs a readable conversation history in the format:

            User: <user_message>
            Assistant: <assistant_message>

        Returns:
            str: A newline-separated string representing the conversation context.
        """
        context_text = ""
        for msg in context_history:
            if isinstance(msg, dict):
                human_msg = msg.get("user")
                system_msg = msg.get("assistant")
                if human_msg:
                    context_text += f"User: {human_msg}\n"
                if system_msg:
                    context_text += f"Assistant: {system_msg}\n"
        
        return context_text

    def sdk_dump_to_json(raw):
        def convert(obj):
            # Basic types
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj

            # Enum → value
            if isinstance(obj, Enum):
                return obj.value

            # List → convert each item
            if isinstance(obj, list):
                return [convert(item) for item in obj]

            # Dict → convert keys & values
            if isinstance(obj, dict):
                return {str(k): convert(v) for k, v in obj.items()}

            # SDK objects (have __dict__)
            if hasattr(obj, "__dict__"):
                data = {}
                for k, v in obj.__dict__.items():
                    # Skip private attributes
                    if k.startswith("_"):
                        continue
                    data[k] = convert(v)
                return data

            # Fallback to string
            return str(obj)

        try:
            # Convert whole response
            result = convert(raw)
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {
                    "error": str(e),
                    "type": str(type(raw))
                },
                indent=2
            )
    
    def extract_sources(response):
        """
        Extracts (title, uri) from response.

        Returns:
            list of dict: Each dict contains {"title": str, "url": str}
        """
        raw_text = str(response)

        titles = re.findall(r"title='([^']+)'", raw_text)
        urls = re.findall(r"uri='([^']+)'", raw_text)

        results = []
        for t, u in zip(titles, urls):
            results.append({"title": t, "url": u})
        return json.dumps(results)



    
