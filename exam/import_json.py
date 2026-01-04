"""
Import JSON data for TOEIC Reading (Part 5, 6, 7) and Listening (Part 1, 2, 3, 4).

JSON Format mới (schema_version 1.0):
{
  "schema_version": "1.0",
  "test_id": "...",
  "module": "READING" | "LISTENING",
  "sections": [
    {
      "section_id": "P5" | "P6" | "P7" | "P1" | "P2" | "P3" | "P4",
      "type": "...",
      "instruction": "...",
      "question_numbers": [...] hoặc "passage_ids": [...]
    }
  ],
  "passages": [
    {
      "passage_id": "...",
      "section_id": "...",
      "type": "...",
      "instruction": "...",
      "question_numbers": [...],
      "assets": [{"kind": "image", "url": "..."}],
      "text": "...",
      "meta": {...}
    }
  ],
  "questions": [
    {
      "question_id": "...",
      "number": 126,
      "section_id": "P5",
      "passage_id": null | "...",
      "question_type": "...",
      "stem": "...",
      "choices": [{"key": "A", "text": "..."}],
      "answer_key": "A" | "B" | "C" | "D",
      "explanation": "...",
      "meta": {...}
    }
  ]
}
"""
import json
import logging
import os
import tempfile
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlretrieve
from django.core.files.base import ContentFile
from .models import (
    ExamTemplate,
    ExamQuestion,
    ReadingPassage,
    ListeningConversation,
    TOEICPart,
    QuestionType,
    ExamCategory,
)

logger = logging.getLogger(__name__)


def download_file_from_url(file_url: str, default_filename: str = "file") -> Optional[ContentFile]:
    """
    Download file từ URL và trả về ContentFile.
    
    Args:
        file_url: URL của file cần download
        default_filename: Tên file mặc định nếu không lấy được từ URL
    
    Returns:
        ContentFile: File object để lưu vào FileField/ImageField
        None: Nếu download thất bại
    """
    try:
        # Parse URL
        parsed = urlparse(file_url)
        if not parsed.scheme or not parsed.netloc:
            logger.warning(f"Invalid URL: {file_url}")
            return None
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            urlretrieve(file_url, tmp_file.name)
            # Read file content
            with open(tmp_file.name, 'rb') as f:
                content = f.read()
            # Get filename from URL
            filename = os.path.basename(parsed.path) or default_filename
            # Clean up temp file
            os.unlink(tmp_file.name)
        
        # Return ContentFile
        return ContentFile(content, name=filename)
    except Exception as e:
        logger.error(f"Error downloading file from {file_url}: {e}")
        return None


def convert_answer_key_to_number(answer_key: str) -> str:
    """
    Convert answer key từ A/B/C/D sang 1/2/3/4 để tương thích với DB.
    
    Args:
        answer_key: "A", "B", "C", "D" hoặc "1", "2", "3", "4"
    
    Returns:
        str: "1", "2", "3", "4"
    """
    mapping = {
        "A": "1",
        "B": "2",
        "C": "3",
        "D": "4",
        "a": "1",
        "b": "2",
        "c": "3",
        "d": "4",
    }
    return mapping.get(answer_key, answer_key)


def convert_choices_keys(choices: list) -> list:
    """
    Convert choices keys từ A/B/C/D sang 1/2/3/4 để tương thích với DB.
    
    Args:
        choices: [{"key": "A", "text": "..."}, ...]
    
    Returns:
        list: [{"key": "1", "text": "..."}, ...]
    """
    converted = []
    for choice in choices:
        new_key = convert_answer_key_to_number(choice.get("key", ""))
        converted.append({
            "key": new_key,
            "text": choice.get("text", "")
        })
    return converted


def create_or_get_template_from_json(json_data: Dict) -> tuple[ExamTemplate, bool]:
    """
    Tự động tạo hoặc lấy ExamTemplate từ JSON data.
    
    Args:
        json_data: Dict parsed từ JSON file
        
    Returns:
        tuple: (ExamTemplate instance, created: bool)
            - created = True nếu template mới được tạo
            - created = False nếu template đã tồn tại
    """
    from .models import ExamLevel, ExamCategory
    
    test_id = json_data.get('test_id', '').strip()
    module = json_data.get('module', '').strip().upper()
    
    # Xác định category dựa trên module
    if module == 'READING':
        category = ExamCategory.READING
    elif module == 'LISTENING':
        category = ExamCategory.LISTENING
    else:
        category = ExamCategory.TOEIC_FULL
    
    # Tìm template theo test_id hoặc title
    template = None
    if test_id:
        # Thử tìm theo slug (nếu test_id có thể convert thành slug)
        from utils.slug import to_romaji_slug
        slug_candidate = to_romaji_slug(test_id)
        template = ExamTemplate.objects.filter(slug=slug_candidate, level=ExamLevel.TOEIC).first()
        
        # Nếu không tìm thấy, thử tìm theo title
        if not template:
            template = ExamTemplate.objects.filter(title__icontains=test_id, level=ExamLevel.TOEIC).first()
    
    # Nếu không tìm thấy, tạo mới
    if not template:
        title = test_id or f"TOEIC {module} Test"
        template = ExamTemplate.objects.create(
            title=title,
            level=ExamLevel.TOEIC,
            category=category,
            is_active=True,
        )
        return template, True
    
    return template, False


def import_toeic_json(template: ExamTemplate, json_data: Dict) -> Dict[str, any]:
    """
    Import TOEIC questions từ JSON data (format mới - schema_version 1.0).
    
    Format mới hỗ trợ:
    - Sections (P5, P6, P7 cho Reading; P1-P4 cho Listening)
    - Passages với assets
    - Questions với metadata đầy đủ
    
    Tự động update category:
    - Nếu có cả Listening và Reading → category = TOEIC_FULL, is_full_toeic = True
    - Nếu chỉ có Listening → category = LISTENING
    - Nếu chỉ có Reading → category = READING
    
    Args:
        template: ExamTemplate instance
        json_data: Dict parsed từ JSON file (format mới)
        
    Returns:
        Dict với keys:
            - "success": bool
            - "message": str
            - "created_passages": int
            - "created_conversations": int
            - "created_questions": int
            - "category_updated": bool
            - "errors": List[str]
    """
    errors = []
    created_passages = 0
    created_conversations = 0
    created_questions = 0
    category_updated = False
    
    try:
        # Validate schema version
        schema_version = json_data.get("schema_version")
        if schema_version != "1.0":
            return {
                "success": False,
                "message": f"Unsupported schema_version: {schema_version}. Only version 1.0 is supported.",
                "created_passages": 0,
                "created_conversations": 0,
                "created_questions": 0,
                "errors": [f"Unsupported schema_version: {schema_version}"]
            }
        
        # Get module (READING or LISTENING)
        module = json_data.get("module", "").upper()
        if module not in ["READING", "LISTENING"]:
            return {
                "success": False,
                "message": f"Invalid module: {module}. Must be 'READING' or 'LISTENING'.",
                "created_passages": 0,
                "created_conversations": 0,
                "created_questions": 0,
                "errors": [f"Invalid module: {module}"]
            }
        
        # Get sections, passages, questions
        sections = json_data.get("sections", [])
        passages_data = json_data.get("passages", [])
        questions_data = json_data.get("questions", [])
        
        if not sections:
            return {
                "success": False,
                "message": "No sections found in JSON",
                "created_passages": 0,
                "created_conversations": 0,
                "created_questions": 0,
                "errors": ["No sections found"]
            }
        
        if not questions_data:
            return {
                "success": False,
                "message": "No questions found in JSON",
                "created_passages": 0,
                "created_conversations": 0,
                "created_questions": 0,
                "errors": ["No questions found"]
            }
        
        # Mapping section_id → toeic_part
        SECTION_TO_PART = {
            "P1": TOEICPart.LISTENING_1,
            "P2": TOEICPart.LISTENING_2,
            "P3": TOEICPart.LISTENING_3,
            "P4": TOEICPart.LISTENING_4,
            "P5": TOEICPart.READING_5,
            "P6": TOEICPart.READING_6,
            "P7": TOEICPart.READING_7,
        }
        
        # ===== STEP 1: Create Passages (for Reading Part 6, 7) =====
        passage_map = {}  # passage_id → ReadingPassage instance
        
        if module == "READING":
            for passage_data in passages_data:
                try:
                    passage_id = passage_data.get("passage_id")
                    section_id = passage_data.get("section_id")
                    
                    if not passage_id:
                        errors.append(f"Passage missing passage_id: {passage_data}")
                        continue
                    
                    if section_id not in ["P6", "P7"]:
                        errors.append(f"Passage {passage_id} has invalid section_id: {section_id}")
                        continue
                    
                    # Get order from question_numbers or meta
                    question_numbers = passage_data.get("question_numbers", [])
                    order = passage_data.get("order")
                    if not order and question_numbers:
                        order = min(question_numbers)
                    if not order:
                        order = len(passage_map) + 1
                    
                    # Create ReadingPassage
                    passage = ReadingPassage.objects.create(
                        template=template,
                        order=order,
                        title=passage_data.get("instruction", ""),
                        text=passage_data.get("text", ""),
                    )
                    
                    # Download image from assets if available
                    assets = passage_data.get("assets", [])
                    for asset in assets:
                        if asset.get("kind") == "image":
                            image_url = asset.get("url")
                            if image_url:
                                image_file = download_file_from_url(image_url, f"passage_{passage_id}.jpg")
                                if image_file:
                                    passage.image.save(
                                        image_file.name,
                                        image_file,
                                        save=True
                                    )
                                    break  # Only use first image
                    
                    passage_map[passage_id] = passage
                    created_passages += 1
                    
                except Exception as e:
                    error_msg = f"Error creating passage {passage_data.get('passage_id')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        # ===== STEP 2: Create Conversations (for Listening Part 3, 4) =====
        conversation_map = {}  # conversation_id → ListeningConversation instance
        
        if module == "LISTENING":
            # Track order per section
            section_order_counters = {"P3": 0, "P4": 0}
            
            # Group passages by section_id to create conversations
            for passage_data in passages_data:
                try:
                    passage_id = passage_data.get("passage_id")
                    section_id = passage_data.get("section_id")
                    
                    if not passage_id:
                        continue
                    
                    if section_id not in ["P3", "P4"]:
                        continue
                    
                    toeic_part = SECTION_TO_PART.get(section_id)
                    if not toeic_part:
                        continue
                    
                    # Get order from question_numbers or use counter
                    question_numbers = passage_data.get("question_numbers", [])
                    order = passage_data.get("order")
                    if not order:
                        section_order_counters[section_id] += 1
                        order = section_order_counters[section_id]
                    
                    # Create ListeningConversation
                    conversation = ListeningConversation.objects.create(
                        template=template,
                        toeic_part=toeic_part,
                        order=order,
                        transcript=passage_data.get("text", ""),
                    )
                    
                    # Download audio from assets if available
                    assets = passage_data.get("assets", [])
                    for asset in assets:
                        if asset.get("kind") == "audio":
                            audio_url = asset.get("url")
                            if audio_url:
                                audio_file = download_file_from_url(audio_url, f"conversation_{passage_id}.mp3")
                                if audio_file:
                                    conversation.audio.save(
                                        audio_file.name,
                                        audio_file,
                                        save=True
                                    )
                                    break
                        
                        if asset.get("kind") == "image":
                            image_url = asset.get("url")
                            if image_url:
                                image_file = download_file_from_url(image_url, f"conversation_{passage_id}.jpg")
                                if image_file:
                                    conversation.image.save(
                                        image_file.name,
                                        image_file,
                                        save=True
                                    )
                    
                    conversation_map[passage_id] = conversation
                    created_conversations += 1
                    
                except Exception as e:
                    error_msg = f"Error creating conversation {passage_data.get('passage_id')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        # ===== STEP 3: Create Questions =====
        for q_data in questions_data:
            try:
                question_id = q_data.get("question_id", "")
                number = q_data.get("number")
                section_id = q_data.get("section_id")
                passage_id = q_data.get("passage_id")
                
                if number is None:
                    errors.append(f"Question {question_id} missing 'number' field")
                    continue
                
                if not section_id:
                    errors.append(f"Question {question_id} missing 'section_id' field")
                    continue
                
                # Map section_id to toeic_part
                toeic_part = SECTION_TO_PART.get(section_id)
                if not toeic_part:
                    errors.append(f"Question {question_id} has invalid section_id: {section_id}")
                    continue
                
                # Get passage or conversation
                passage = None
                listening_conversation = None
                
                if module == "READING" and passage_id:
                    passage = passage_map.get(passage_id)
                    if not passage:
                        errors.append(f"Question {question_id} references unknown passage_id: {passage_id}")
                        continue
                
                if module == "LISTENING" and passage_id:
                    listening_conversation = conversation_map.get(passage_id)
                    if not listening_conversation:
                        errors.append(f"Question {question_id} references unknown passage_id: {passage_id}")
                        continue
                
                # Convert choices keys from A/B/C/D to 1/2/3/4
                choices = q_data.get("choices", [])
                converted_choices = convert_choices_keys(choices)
                
                # Convert answer_key from A/B/C/D to 1/2/3/4
                answer_key = q_data.get("answer_key", "")
                correct_answer = convert_answer_key_to_number(answer_key)
                
                if not correct_answer:
                    errors.append(f"Question {question_id} missing or invalid 'answer_key'")
                    continue
                
                # Create ExamQuestion
                question = ExamQuestion.objects.create(
                    template=template,
                    toeic_part=toeic_part,
                    order=number,
                    text=q_data.get("stem", ""),
                    question_type=QuestionType.MCQ,
                    data={
                        "choices": converted_choices
                    },
                    correct_answer=correct_answer,
                    explanation_vi=q_data.get("explanation", ""),
                    passage=passage,
                    listening_conversation=listening_conversation,
                )
                
                # Download image/audio for Part 1, 2 if needed
                if module == "LISTENING" and section_id in ["P1", "P2"]:
                    # Check if question has assets in meta or need to download from passage
                    # For now, we'll skip individual question assets in new format
                    # They should be handled via passages for Part 3, 4
                    pass
                
                created_questions += 1
                
            except Exception as e:
                error_msg = f"Error creating question {q_data.get('question_id', q_data.get('number'))}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # ===== STEP 4: Auto-update category =====
        # Check existing questions to determine current parts
        existing_questions = template.questions.filter(toeic_part__isnull=False).values_list('toeic_part', flat=True).distinct()
        existing_parts = set(existing_questions)
        
        # Add parts we just imported
        imported_sections = set(s.get("section_id") for s in sections)
        for section_id in imported_sections:
            toeic_part = SECTION_TO_PART.get(section_id)
            if toeic_part:
                existing_parts.add(toeic_part)
        
        # Determine if we have both Listening and Reading
        has_listening = any(p.startswith('L') for p in existing_parts)
        has_reading = any(p.startswith('R') for p in existing_parts)
        
        # Update category if needed
        old_category = template.category
        if has_listening and has_reading:
            # Full test: both Listening and Reading
            if template.category != ExamCategory.TOEIC_FULL:
                template.category = ExamCategory.TOEIC_FULL
                template.is_full_toeic = True
                template.save(update_fields=['category', 'is_full_toeic'])
                category_updated = True
        elif has_listening:
            # Only Listening
            if template.category != ExamCategory.LISTENING:
                template.category = ExamCategory.LISTENING
                template.is_full_toeic = False
                template.save(update_fields=['category', 'is_full_toeic'])
                category_updated = True
        elif has_reading:
            # Only Reading
            if template.category != ExamCategory.READING:
                template.category = ExamCategory.READING
                template.is_full_toeic = False
                template.save(update_fields=['category', 'is_full_toeic'])
                category_updated = True
        
        success = len(errors) == 0
        message = f"Successfully imported {created_questions} questions"
        if created_passages > 0:
            message += f" and {created_passages} passages"
        if created_conversations > 0:
            message += f" and {created_conversations} conversations"
        
        if category_updated:
            message += f". Category đã tự động cập nhật: {old_category} → {template.get_category_display()}"
        
        return {
            "success": success,
            "message": message,
            "created_passages": created_passages,
            "created_conversations": created_conversations,
            "created_questions": created_questions,
            "category_updated": category_updated,
            "errors": errors
        }
    
    except Exception as e:
        error_msg = f"Error importing JSON: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "message": error_msg,
            "created_passages": created_passages,
            "created_conversations": created_conversations,
            "created_questions": created_questions,
            "category_updated": False,
            "errors": [error_msg]
        }


# Alias để backward compatibility (deprecated)
def import_reading_json(template: ExamTemplate, json_data: Dict) -> Dict[str, any]:
    """Alias for import_toeic_json (deprecated - use import_toeic_json instead)."""
    return import_toeic_json(template, json_data)
