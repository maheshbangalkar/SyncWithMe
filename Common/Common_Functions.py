import json
import re
from enum import Enum
from typing import Any, Dict, List, Union


class CommonFunctions:
    """
    Utility helpers used across the project.

    Methods are static so you can import the class and call directly:
        from Common.Common_Functions import CommonFunctions as common
        common.build_context_text(...)
    """

    @staticmethod
    def make_serializable(obj: Any) -> Any:
        """
        Recursively convert objects to JSON-serializable forms.
        Non-serializable objects are converted to strings.
        """
        # Basic JSON types are returned as-is
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        # Enum -> value
        if isinstance(obj, Enum):
            return obj.value

        # List/tuple -> convert each element
        if isinstance(obj, (list, tuple)):
            return [CommonFunctions.make_serializable(v) for v in obj]

        # Dict -> convert keys and values
        if isinstance(obj, dict):
            return {str(k): CommonFunctions.make_serializable(v) for k, v in obj.items()}

        # Objects with __dict__ (SDK objects) -> convert their public attrs
        if hasattr(obj, "__dict__"):
            out = {}
            for k, v in vars(obj).items():
                if k.startswith("_"):
                    continue
                out[k] = CommonFunctions.make_serializable(v)
            return out

        # Fallback: try JSON dump, otherwise string
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)

    @staticmethod
    def format_template(template: Union[list, dict, str], updates: Dict[str, Any]) -> str:
        """
        Copy a template and update it with values from `updates`.
        - If template is a list and first element is a dict, it updates that dict.
        - If template is a dict, it updates it.
        - If template is a string, it performs simple replacement of keys wrapped in {{key}}.
        Returns a JSON string for list/dict templates, or the formatted string.
        """
        if isinstance(template, list):
            # make a shallow copy
            formatted = [item.copy() if isinstance(item, dict) else item for item in template]
            if formatted and isinstance(formatted[0], dict):
                formatted[0].update({k: CommonFunctions.make_serializable(v) for k, v in updates.items()})
            return json.dumps(formatted, ensure_ascii=False)

        if isinstance(template, dict):
            formatted = template.copy()
            formatted.update({k: CommonFunctions.make_serializable(v) for k, v in updates.items()})
            return json.dumps(formatted, ensure_ascii=False)

        if isinstance(template, str):
            result = template
            # simple templating: replace {{key}} with str(value)
            for k, v in updates.items():
                result = result.replace(f"{{{{{k}}}}}", str(v))
            return result

        # Unknown type — return stringified
        return json.dumps({"template": str(template), "updates": updates}, ensure_ascii=False)

    @staticmethod
    def build_context_text(context_history: List[Dict[str, str]]) -> str:
        """
        Build a newline-separated conversation context string from a list of messages.
        Each message is expected to be a dict with optional keys: 'user', 'assistant'.
        """
        lines: List[str] = []
        for msg in context_history or []:
            if not isinstance(msg, dict):
                continue
            user_msg = msg.get("user")
            assistant_msg = msg.get("assistant")
            if user_msg:
                lines.append(f"User: {user_msg}")
            if assistant_msg:
                lines.append(f"Assistant: {assistant_msg}")
        return "\n".join(lines).strip()

    @staticmethod
    def sdk_dump_to_json(raw: Any) -> str:
        """
        Safely convert an SDK response (or any complex object) into a JSON string.
        Handles enums, lists, dicts, and objects with __dict__ recursively.
        """
        def convert(obj: Any) -> Any:
            # None and primitives
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj

            # Enum
            if isinstance(obj, Enum):
                return obj.value

            # List/tuple
            if isinstance(obj, (list, tuple)):
                return [convert(i) for i in obj]

            # Dict
            if isinstance(obj, dict):
                return {str(k): convert(v) for k, v in obj.items()}

            # Objects with __dict__
            if hasattr(obj, "__dict__"):
                out = {}
                for k, v in vars(obj).items():
                    if k.startswith("_"):
                        continue
                    out[k] = convert(v)
                return out

            # Fallback to string
            try:
                return str(obj)
            except Exception:
                return {"unserializable_type": str(type(obj))}

        try:
            converted = convert(raw)
            return json.dumps(converted, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e), "type": str(type(raw))}, indent=2)

    @staticmethod
    def extract_sources(response: Any) -> List[Dict[str, str]]:
        """
        Extract sources (title, uri) from a response's string representation.
        Returns a list of {"title": ..., "url": ...} dictionaries.
        This is a best-effort parser that looks for common patterns.
        """
        text = ""
        try:
            # Prefer structured fields if present
            if hasattr(response, "candidates") and response.candidates:
                # Try to pull from candidate content metadata if available
                for cand in response.candidates:
                    # attempt to get source metadata
                    # many SDK responses embed source info in .metadata or .content
                    if hasattr(cand, "content") and hasattr(cand.content, "metadata"):
                        meta = getattr(cand.content, "metadata", None)
                        if isinstance(meta, dict):
                            # try to extract title/url pairs
                            titles = meta.get("titles") or meta.get("title")
                            uri = meta.get("uri") or meta.get("url")
                            if uri:
                                return [{"title": titles or str(uri), "url": uri}]
                # fallback to stringifying
                text = str(response)
            else:
                text = str(response)
        except Exception:
            text = str(response)

        # regex extraction fallback
        titles = re.findall(r"title=['\"]([^'\"]+)['\"]", text)
        urls = re.findall(r"(?:uri|url|link)=['\"]([^'\"]+)['\"]", text)

        results: List[Dict[str, str]] = []
        for t, u in zip(titles, urls):
            results.append({"title": t, "url": u})

        # If no pairs found, return empty list
        return results
