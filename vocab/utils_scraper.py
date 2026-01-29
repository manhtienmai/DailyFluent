import requests
from bs4 import BeautifulSoup
from django.conf import settings

def scrape_cambridge(word):
    """
    Cào dữ liệu từ Cambridge Dictionary.
    Trả về list các dict:
    {
        'type': 'noun',
        'ipa': '/.../',
        'audio_uk': 'url',
        'audio_us': 'url',
        'definition': '...',
        'example': '...'
    }
    """
    url = f"https://dictionary.cambridge.org/dictionary/english/{word}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        read_timeout = getattr(settings, 'AZURE_READ_TIMEOUT', 30)
        response = requests.get(url, headers=headers, timeout=read_timeout)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Cambridge often changes structure, but usually .entry-body__el or .pr is the entry wrapper
        entries = soup.select('.pr.entry-body__el')
        
        # --- Fallback Strategy ---
        if not entries:
            # Try finding ANY valid content via global search
            data = {
                'type': '',
                'ipa': '',
                'audio_uk': None,
                'audio_us': None,
                'definition': '',
                'example': ''
            }
            
            # 1. POS
            pos_el = soup.select_one('.pos')
            if pos_el: data['type'] = pos_el.text.strip()
            
            # 2. Audio (Global Search)
            sources = soup.select('source[type="audio/mpeg"]')
            for s in sources:
                src = s.get('src', '')
                if not src: continue
                if not src.startswith('http'):
                    src = "https://dictionary.cambridge.org" + src
                
                if 'uk_pron' in src and not data['audio_uk']:
                    data['audio_uk'] = src
                elif 'us_pron' in src and not data['audio_us']:
                    data['audio_us'] = src
            
            # 3. IPA
            ipa_el = soup.select_one('.ipa')
            if ipa_el: data['ipa'] = f"/{ipa_el.text.strip()}/"
                
            # 4. Definition (English)
            def_el = soup.select_one('.def')
            if def_el:
                data['definition'] = def_el.text.strip().rstrip(':')
                
            # Example
            ex_el = soup.select_one('.eg')
            if ex_el:
                data['example'] = ex_el.text.strip()
            
            if data['definition'] or data['audio_us']:
                 results.append(data)
                 return results

        # --- Standard Strategy (Entry Loop) ---
        for entry in entries[:5]:
            data = {
                'type': '',
                'ipa': '',
                'audio_uk': None,
                'audio_us': None,
                'definition': '',
                'example': ''
            }
            
            pos_tag = entry.select_one('.pos-header .pos') or entry.select_one('.pos')
            if pos_tag:
                data['type'] = pos_tag.text.strip()
            
            # ... Audio/IPA logic identical to before, just ensuring selectors match ...
            
            # UK
            uk_span = entry.select_one('.uk.dpron-i')
            if uk_span:
                ipa = uk_span.select_one('.ipa')
                if ipa: data['ipa'] = f"/{ipa.text.strip()}/"
                src = uk_span.select_one('source[type="audio/mpeg"]')
                if src and src.get('src'):
                    data['audio_uk'] = "https://dictionary.cambridge.org" + src['src']

            # US
            us_span = entry.select_one('.us.dpron-i')
            if us_span:
                # prioritize US IPA if needed, typically same
                src = us_span.select_one('source[type="audio/mpeg"]')
                if src and src.get('src'):
                    data['audio_us'] = "https://dictionary.cambridge.org" + src['src']

            # Definition (English)
            # Structure: .def-block -> .ddef_h -> .def
            def_block = entry.select_one('.def-block')
            if def_block:
                ddef = def_block.select_one('.def') # English definition
                if ddef:
                    data['definition'] = ddef.text.strip().rstrip(':')
                
                eg = def_block.select_one('.examp .eg')
                if eg:
                    data['example'] = eg.text.strip()

            if data['definition'] or data['audio_us']:
                results.append(data)
        
        return results
    except Exception:
        return []
