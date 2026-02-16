import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    _models = {}  # cache by model name
    _configured = False

    @classmethod
    def _configure(cls):
        if not cls._configured:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                logger.warning("GEMINI_API_KEY is not set.")
                return False
            genai.configure(api_key=api_key)
            cls._configured = True
        return True

    @classmethod
    def get_model(cls, model_name=None):
        model_name = model_name or 'gemini-2.5-pro'
        if model_name not in cls._models:
            if not cls._configure():
                return None
            cls._models[model_name] = genai.GenerativeModel(model_name)
        return cls._models[model_name]

    @classmethod
    def generate_text(cls, prompt, model_name=None):
        """
        Generates text using the specified Gemini model.
        Defaults to gemini-2.5-pro.
        """
        try:
            model = cls.get_model(model_name)
            if not model:
                return "Error: API Key not configured."

            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return f"Error: {str(e)}"
