from django.core.management.base import BaseCommand
from vocab.services.gemini_service import GeminiService
import time

class Command(BaseCommand):
    help = 'Tests the Gemini AI integration'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Testing Gemini AI Integration...'))
        
        start_time = time.time()
        response = GeminiService.generate_text("Hello Gemini, tell me a fun fact about language learning in one sentence.")
        end_time = time.time()
        
        self.stdout.write(f"Response ({end_time - start_time:.2f}s):")
        self.stdout.write(self.style.SUCCESS(response))
