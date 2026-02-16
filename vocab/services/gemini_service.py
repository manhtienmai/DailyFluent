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
        model_name = model_name or 'gemini-2.5-flash'
        if model_name not in cls._models:
            if not cls._configure():
                return None
            cls._models[model_name] = genai.GenerativeModel(model_name)
        return cls._models[model_name]

    @classmethod
    def generate_with_image(cls, prompt, image_bytes, mime_type='image/png', model_name=None):
        """Send image + text prompt to Gemini for vision tasks (OCR, analysis)."""
        try:
            model = cls.get_model(model_name or 'gemini-2.5-flash')
            if not model:
                return "Error: API Key not configured."
            image_part = {'mime_type': mime_type, 'data': image_bytes}
            response = model.generate_content([prompt, image_part])
            return response.text
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
            return f"Error: {str(e)}"

    @classmethod
    def generate_image(cls, prompt, ref_image_bytes=None, mime_type='image/png', model_name=None):
        """Generate image using Gemini. Returns (image_bytes, mime_type) or (None, error_msg)."""
        try:
            model = cls.get_model(model_name or 'gemini-2.5-flash-image')
            if not model:
                return None, "Error: API Key not configured."
            parts = [prompt]
            if ref_image_bytes:
                parts.append({'mime_type': mime_type, 'data': ref_image_bytes})
            response = model.generate_content(
                parts,
                generation_config={'response_modalities': ['IMAGE', 'TEXT']}
            )
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                    return part.inline_data.data, part.inline_data.mime_type
            return None, "No image in response"
        except Exception as e:
            logger.error(f"Gemini image generation error: {e}")
            return None, f"Error: {str(e)}"

    @classmethod
    def generate_text(cls, prompt, model_name=None):
        """
        Generates text using the specified Gemini model.
        Defaults to gemini-2.5-flash.
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
