import google.generativeai as genai
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                logger.warning("GEMINI_API_KEY is not set.")
                return None
            
            genai.configure(api_key=api_key)
            cls._model = genai.GenerativeModel('gemini-1.5-flash')
        return cls._model

    @classmethod
    def generate_text(cls, prompt):
        """
        Generates text using the Gemini 1.5 Flash model.
        Returns the text content or None if generation fails.
        """
        try:
            model = cls.get_model()
            if not model:
                return "Error: API Key not configured."
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return f"Error: {str(e)}"
