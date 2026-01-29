import time
import requests
import re
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from bs4 import BeautifulSoup
from django.conf import settings
from vocab.models import Vocabulary, WordEntry, WordDefinition
from vocab.utils_scraper import scrape_cambridge


def normalize_filename(word, pos, accent):
    """
    Standardize filename: audio/en/{word}_{pos}_{accent}.mp3
    Example: audio/en/record_noun_us.mp3
    """
    clean_word = re.sub(r'[^a-zA-Z0-9_]', '', word.lower().replace(' ', '_'))
    clean_pos = re.sub(r'[^a-zA-Z0-9_]', '', pos.lower().replace(' ', '_'))
    return f"audio/en/{clean_word}_{clean_pos}_{accent}.mp3"


def upload_with_timeout(filename, content, timeout=None):
    """Upload to storage with timeout to prevent hanging."""
    if timeout is None:
        timeout = getattr(settings, 'AZURE_CONNECTION_TIMEOUT', 60)
        
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(default_storage.save, filename, content)
        try:
            result = future.result(timeout=timeout)
            return result, None
        except FutureTimeoutError:
            return None, f"Upload timeout after {timeout}s"
        except Exception as e:
            return None, str(e)


def download_and_upload(url, filename, stdout=None):
    """
    Download audio from URL and upload to Storage (Azure).
    Returns the storage URL.
    """
    if not url:
        return None
        
    try:
        if stdout: stdout.write(f"      > Downloading: {url}...")
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        read_timeout = getattr(settings, 'AZURE_READ_TIMEOUT', 30)
        res = requests.get(url, headers=headers, timeout=read_timeout)
        
        if res.status_code == 200:
            if stdout: stdout.write(f"      > Uploading ({len(res.content)} bytes)...")
            
            # Upload with timeout to prevent hanging
            saved_path, error = upload_with_timeout(filename, ContentFile(res.content))
            
            if saved_path:
                try:
                    file_url = default_storage.url(saved_path)
                    if stdout: stdout.write(f"      > ✓ Uploaded successfully")
                    return file_url
                except Exception as url_error:
                    if stdout: stdout.write(f"      > ✗ Get URL failed: {str(url_error)[:50]}")
                    return url
            else:
                if stdout: stdout.write(f"      > ✗ Upload failed: {error[:80]}")
                if stdout: stdout.write(f"      > Using original URL instead")
                return url  # Fallback to original URL
        else:
            if stdout: stdout.write(f"      > Download failed (HTTP {res.status_code})")
            
    except requests.Timeout:
        if stdout: stdout.write(f"   [WARN] Download timeout for {filename}")
        return url
    except Exception as e:
        if stdout: stdout.write(f"   [WARN] Error: {str(e)[:100]}")
        return url
        
    return url


class Command(BaseCommand):
    help = 'Cào dữ liệu (IPA, Audio, Nghĩa) và Upload Audio lên Azure'

    def add_arguments(self, parser):
        parser.add_argument('words', nargs='+', type=str, help='Danh sách từ vựng')
        parser.add_argument('--no-upload', action='store_true', help='Skip Azure upload, use original URLs')

    def handle(self, *args, **kwargs):
        words_input = kwargs['words']
        skip_upload = kwargs.get('no_upload', False)
        
        if skip_upload:
            self.stdout.write("[MODE] Skipping Azure upload - using original URLs")
        
        self.stdout.write(f"[START] Processing {len(words_input)} words: {', '.join(words_input)}")

        for word_text in words_input:
            clean_word = word_text.strip().lower()
            
            # 1. Tìm/Tạo Vocabulary
            vocab, created = Vocabulary.objects.get_or_create(
                word=clean_word,
                defaults={'language': Vocabulary.Language.ENGLISH}
            )
            
            status = "[NEW]" if created else "[UPDATE]"
            self.stdout.write(f"--- {status}: '{clean_word}' ---")

            try:
                # 2. Cào dữ liệu
                self.stdout.write("   > Scraping Cambridge...")
                scraped_entries = scrape_cambridge(clean_word)
                self.stdout.write(f"   > Scrape done. Found {len(scraped_entries)} entries in Top 5.")

                if scraped_entries:
                    entry_count = 0
                    def_count = 0
                    
                    for i, item in enumerate(scraped_entries):
                        pos = item['type'] or 'unknown'
                        self.stdout.write(f"   > Processing Entry {i+1}: {pos}")
                        
                        # --- PROCESS AUDIO (Download & Upload) ---
                        if not skip_upload:
                            # US
                            if item['audio_us']:
                                fname = normalize_filename(clean_word, pos, 'us')
                                new_url = download_and_upload(item['audio_us'], fname, self.stdout)
                                if new_url:
                                    item['audio_us'] = new_url
                            
                            # UK
                            if item['audio_uk']:
                                fname = normalize_filename(clean_word, pos, 'uk')
                                new_url = download_and_upload(item['audio_uk'], fname, self.stdout)
                                if new_url:
                                    item['audio_uk'] = new_url
                        else:
                            self.stdout.write(f"   > Skipping upload, using original URLs")
                        # ----------------------------------------
                        
                        # 3. Tạo/Update WordEntry

                        entry, entry_created = WordEntry.objects.get_or_create(
                            vocab=vocab,
                            part_of_speech=pos,
                            defaults={
                                'ipa': item['ipa'],
                                'audio_us': item['audio_us'] or '',
                                'audio_uk': item['audio_uk'] or ''
                            }
                        )
                        
                        if not entry_created:
                            updated = False
                            if not entry.ipa and item['ipa']:
                                entry.ipa = item['ipa']
                                updated = True
                            # Force update audio if new one is available (likely Azure Link now)
                            if item['audio_us'] and entry.audio_us != item['audio_us']:
                                entry.audio_us = item['audio_us']
                                updated = True
                            if item['audio_uk'] and entry.audio_uk != item['audio_uk']:
                                entry.audio_uk = item['audio_uk']
                                updated = True
                                
                            if updated:
                                entry.save()
                        else:
                            entry_count += 1
                        
                        # 4. Tạo WordDefinition
                        if not entry.definitions.filter(meaning=item['definition']).exists():
                            WordDefinition.objects.create(
                                entry=entry,
                                meaning=item['definition'],
                                example_sentence=item['example']
                            )
                            def_count += 1
                    
                    if entry_count > 0:
                        self.stdout.write(f"   + Added {entry_count} entries.")
                    if def_count > 0:
                        self.stdout.write(f"   + Added {def_count} definitions.")
                    
                    for e in vocab.entries.all():
                        ipa_safe = e.ipa.encode('ascii', 'replace').decode('ascii') if e.ipa else ''
                        self.stdout.write(f"   -> {e.part_of_speech}: {ipa_safe}")
                    
                    self.stdout.write(self.style.SUCCESS(f"[OK] Done: {clean_word}"))
                else:
                    self.stdout.write(self.style.WARNING(f"[NOT FOUND] '{clean_word}'"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[ERROR] Processing '{clean_word}': {e}"))

            if len(words_input) > 1:
                time.sleep(1)


