"""
Import JSON data for TOEIC Reading (Part 5, 6, 7) and Listening (Part 1, 2, 3, 4).

Supports two schema versions:

JSON Format (schema_version 1.0):
{
  "schema_version": "1.0",
  "test_id": "...",
  "module": "READING" | "LISTENING",
  "sections": [...],
  "passages": [{"passage_id": "...", "text": "...", ...}],
  "questions": [{"stem": "...", "choices": [{key, text}], "answer_key": "A"}]
}

JSON Format (schema_version 2.1):
{
  "schema_version": "2.1",
  "test_id": "...",
  "module": "READING" | "LISTENING",
  "sections": [
    {
      "section_id": "P5" | "P6" | "P7",
      "type": "incomplete_sentences" | "text_completion" | "reading_comprehension",
      "instruction": "...",
      "question_numbers": [...] or "passage_ids": [...]
    }
  ],
  "passages": [
    {
      "passage_id": "...",
      "section_id": "P6",
      "content_segments": [{"type": "text"|"blank", "text": "...", "id": "131"}],
      ...
    }
  ],
  "questions": [
    {
      "question_id": "Q101",
      "number": 101,
      "section_id": "P5",
      "stem_segments": [{"type": "text"|"blank", "text": "...", "id": "b101"}],
      "blanks": [{"id": "b101", "choices": [{key, text}], "answer_key": "C"}]
    },
    // P6 questions reference passages, blanks in passage
    {
      "question_id": "Q131",
      "number": 131,
      "section_id": "P6",
      "passage_id": "...",
      "blanks": [{"id": "131", "choices": [{key, text}], "answer_key": "D"}]
    },
    // P7 questions have stem_segments for the question text
    {
      "question_id": "Q147",
      "number": 147,
      "section_id": "P7",
      "passage_id": "...",
      "stem_segments": [{"type": "text", "text": "What is NOT offered?"}],
      "choices": [{key, text}],
      "answer_key": "D"
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


def parse_segments_to_text(segments: list) -> str:
    """
    Convert stem_segments or content_segments array to plain text.
    Blanks are replaced with _____ in the text.
    
    Args:
        segments: List of segment objects, each with 'type' and optionally 'text' or 'id'
                  e.g., [{"type": "text", "text": "The car is"}, {"type": "blank", "id": "b101"}, ...]
    
    Returns:
        str: Plain text with _____ for blanks
    """
    if not segments:
        return ""
    
    result = []
    for segment in segments:
        seg_type = segment.get("type", "text")
        if seg_type == "blank":
            result.append("_____")
        else:
            result.append(segment.get("text", ""))
    
    return "".join(result)


def extract_choices_from_blanks(blanks: list) -> tuple[list, str]:
    """
    Extract choices array and answer_key from blanks field (schema 2.1).
    
    Schema 2.1 stores choices in blanks[0].choices and answer_key in blanks[0].answer_key.
    
    Args:
        blanks: List of blank objects, e.g., [{"id": "b101", "choices": [...], "answer_key": "C"}]
    
    Returns:
        tuple: (choices_list, answer_key)
            - choices_list: [{"key": "1", "text": "..."}, ...]
            - answer_key: "1", "2", "3", or "4"
    """
    if not blanks:
        return [], ""
    
    # Get first blank (most questions have single blank)
    first_blank = blanks[0]
    choices = first_blank.get("choices", [])
    answer_key = first_blank.get("answer_key", "")
    
    # Convert choices keys from A/B/C/D to 1/2/3/4
    converted_choices = convert_choices_keys(choices)
    converted_answer = convert_answer_key_to_number(answer_key)
    
    return converted_choices, converted_answer


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
    Import TOEIC questions từ JSON data (supports schema_version 1.0 and 2.1).
    
    Format hỗ trợ:
    - Schema 1.0: stem/choices format
    - Schema 2.1: stem_segments/blanks format
    - Sections (P5, P6, P7 cho Reading; P1-P4 cho Listening)
    - Passages với assets
    - Questions với metadata đầy đủ
    
    Tự động update category:
    - Nếu có cả Listening và Reading → category = TOEIC_FULL, is_full_toeic = True
    - Nếu chỉ có Listening → category = LISTENING
    - Nếu chỉ có Reading → category = READING
    
    Args:
        template: ExamTemplate instance
        json_data: Dict parsed từ JSON file
        
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
        # Validate schema version - support both 1.0 and 2.1
        schema_version = json_data.get("schema_version")
        if schema_version not in ["1.0", "2.1"]:
            return {
                "success": False,
                "message": f"Unsupported schema_version: {schema_version}. Supported versions: 1.0, 2.1.",
                "created_passages": 0,
                "created_conversations": 0,
                "created_questions": 0,
                "errors": [f"Unsupported schema_version: {schema_version}"]
            }
        
        is_schema_v2 = schema_version == "2.1"

        
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
        section_instruction_map = {s.get("section_id"): s.get("instruction", "") for s in sections if s.get("section_id")}
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
                    
                    # Handle content_segments (schema 2.1) or text (schema 1.0)
                    content_segments = passage_data.get("content_segments", [])
                    if is_schema_v2 and content_segments:
                        # Schema 2.1: convert segments to plain text, store segments in data
                        passage_text = parse_segments_to_text(content_segments)
                        passage_data_field = {"content_segments": content_segments}
                    else:
                        # Schema 1.0: use text field directly
                        passage_text = passage_data.get("text", "")
                        passage_data_field = {}
                    
                    # Create ReadingPassage
                    passage = ReadingPassage.objects.create(
                        template=template,
                        order=order,
                        title=passage_data.get("title", passage_data.get("instruction", "")),
                        text=passage_text,
                        data=passage_data_field,
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
                        # For P7, allow questions to create a placeholder passage when not provided
                        if section_id == "P7":
                            order = number
                            placeholder_title = section_instruction_map.get(section_id) or f"Passage {passage_id}"
                            passage = ReadingPassage.objects.create(
                                template=template,
                                order=order,
                                title=placeholder_title,
                                text="",
                                data={},
                            )
                            passage_map[passage_id] = passage
                            created_passages += 1
                        else:
                            errors.append(f"Question {question_id} references unknown passage_id: {passage_id}")
                            continue
                
                if module == "LISTENING" and passage_id:
                    listening_conversation = conversation_map.get(passage_id)
                    if not listening_conversation:
                        errors.append(f"Question {question_id} references unknown passage_id: {passage_id}")
                        continue
                
                # Handle schema 2.1 (stem_segments + blanks) or schema 1.0 (stem + choices)
                stem_segments = q_data.get("stem_segments", [])
                blanks = q_data.get("blanks", [])
                
                if is_schema_v2 and blanks:
                    # Schema 2.1: Extract choices and answer_key from blanks
                    converted_choices, correct_answer = extract_choices_from_blanks(blanks)
                    
                    # Get stem text from stem_segments or empty if not present
                    if stem_segments:
                        stem_text = parse_segments_to_text(stem_segments)
                    else:
                        stem_text = ""
                    
                    # Store original segments in data for UI rendering
                    question_data = {
                        "choices": converted_choices,
                    }
                    if stem_segments:
                        question_data["stem_segments"] = stem_segments
                    if blanks:
                        question_data["blanks"] = blanks
                    
                elif is_schema_v2 and q_data.get("choices"):
                    # Schema 2.1 P7 questions: have stem_segments but choices/answer_key at top level
                    choices = q_data.get("choices", [])
                    converted_choices = convert_choices_keys(choices)
                    answer_key = q_data.get("answer_key", "")
                    correct_answer = convert_answer_key_to_number(answer_key)
                    
                    if stem_segments:
                        stem_text = parse_segments_to_text(stem_segments)
                    else:
                        stem_text = ""
                    
                    question_data = {
                        "choices": converted_choices,
                    }
                    if stem_segments:
                        question_data["stem_segments"] = stem_segments
                else:
                    # Schema 1.0: Use stem and choices directly
                    choices = q_data.get("choices", [])
                    converted_choices = convert_choices_keys(choices)
                    answer_key = q_data.get("answer_key", "")
                    correct_answer = convert_answer_key_to_number(answer_key)
                    stem_text = q_data.get("stem", "")
                    question_data = {"choices": converted_choices}
                
                if not correct_answer:
                    errors.append(f"Question {question_id} missing or invalid 'answer_key'")
                    continue
                
                # Create ExamQuestion
                question = ExamQuestion.objects.create(
                    template=template,
                    toeic_part=toeic_part,
                    order=number,
                    text=stem_text,
                    question_type=QuestionType.MCQ,
                    data=question_data,
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


def import_bilingual_listening_json(template: ExamTemplate, json_data: list) -> Dict[str, any]:
    """
    Import TOEIC Listening questions với bilingual transcripts từ JSON.
    
    Format JSON: List các objects với type="single" hoặc type="group"
    """
    errors = []
    created_questions = 0
    updated_questions = 0
    created_conversations = 0
    
    try:
        if not isinstance(json_data, list):
            return {
                "success": False,
                "message": "JSON phải là một mảng (list) các câu hỏi",
                "created_questions": 0,
                "updated_questions": 0,
                "errors": ["JSON format không hợp lệ"]
            }
        
        for item in json_data:
            try:
                item_type = item.get("type", "single")
                
                if item_type == "single":
                    q_num = item.get("question_number")
                    if not q_num:
                        errors.append("Question thiếu question_number")
                        continue
                    
                    # Determine TOEIC part
                    if q_num <= 6:
                        toeic_part = TOEICPart.LISTENING_1
                    else:
                        toeic_part = TOEICPart.LISTENING_2
                    
                    # Prepare options data với translations
                    options = item.get("options", [])
                    options_data = [
                        {
                            "label": opt.get("label", ""),
                            "text": opt.get("text", ""),
                            "text_vi": opt.get("text_vi", ""),
                        }
                        for opt in options
                    ]
                    
                    # Check if question exists
                    existing = ExamQuestion.objects.filter(
                        template=template,
                        order=q_num
                    ).first()
                    
                    if existing:
                        existing.audio_transcript = item.get("audio_transcript", "")
                        existing.audio_transcript_vi = item.get("audio_transcript_vi", "")
                        existing.transcript_data = {"options": options_data}
                        existing.toeic_part = toeic_part
                        existing.save()
                        updated_questions += 1
                    else:
                        ExamQuestion.objects.create(
                            template=template,
                            order=q_num,
                            toeic_part=toeic_part,
                            question_type=QuestionType.MCQ,
                            audio_transcript=item.get("audio_transcript", ""),
                            audio_transcript_vi=item.get("audio_transcript_vi", ""),
                            transcript_data={"options": options_data},
                            correct_answer="1",
                        )
                        created_questions += 1
                
                elif item_type == "group":
                    group_range = item.get("group_range", "")
                    questions = item.get("questions", [])
                    
                    if not questions:
                        errors.append(f"Group {group_range} không có câu hỏi")
                        continue
                    
                    # Parse range
                    try:
                        first_q = int(group_range.split("-")[0])
                    except (ValueError, IndexError):
                        first_q = questions[0].get("question_number", 0)
                    
                    # Determine TOEIC part
                    if first_q <= 70:
                        toeic_part = TOEICPart.LISTENING_3
                    else:
                        toeic_part = TOEICPart.LISTENING_4
                    
                    # Calculate conversation order
                    if toeic_part == TOEICPart.LISTENING_3:
                        conv_order = (first_q - 32) // 3 + 1
                    else:
                        conv_order = (first_q - 71) // 3 + 1
                    
                    # Parse transcript into lines
                    transcript = item.get("conversation_transcript", "")
                    transcript_vi = item.get("conversation_transcript_vi", "")
                    lines_data = _parse_transcript_lines(transcript, transcript_vi)
                    
                    # Create or update ListeningConversation
                    conversation, conv_created = ListeningConversation.objects.update_or_create(
                        template=template,
                        toeic_part=toeic_part,
                        order=conv_order,
                        defaults={
                            "transcript": transcript,
                            "transcript_vi": transcript_vi,
                            "transcript_data": {"lines": lines_data},
                        }
                    )
                    
                    if conv_created:
                        created_conversations += 1
                    
                    # Process each question in group
                    for q_item in questions:
                        q_num = q_item.get("question_number")
                        if not q_num:
                            continue
                        
                        options = q_item.get("options", [])
                        options_data = [
                            {
                                "label": opt.get("label", ""),
                                "text": opt.get("text", ""),
                                "text_vi": opt.get("text_vi", ""),
                            }
                            for opt in options
                        ]
                        
                        existing = ExamQuestion.objects.filter(
                            template=template,
                            order=q_num
                        ).first()
                        
                        if existing:
                            existing.text = q_item.get("question_text", "")
                            existing.text_vi = q_item.get("question_text_vi", "")
                            existing.transcript_data = {"options": options_data}
                            existing.toeic_part = toeic_part
                            existing.listening_conversation = conversation
                            existing.save()
                            updated_questions += 1
                        else:
                            ExamQuestion.objects.create(
                                template=template,
                                order=q_num,
                                toeic_part=toeic_part,
                                question_type=QuestionType.MCQ,
                                listening_conversation=conversation,
                                text=q_item.get("question_text", ""),
                                text_vi=q_item.get("question_text_vi", ""),
                                transcript_data={"options": options_data},
                                correct_answer="1",
                            )
                            created_questions += 1
            
            except Exception as e:
                errors.append(f"Error processing item: {str(e)}")
                logger.error(f"Error processing item: {str(e)}")
        
        message = f"Imported {created_questions} câu mới, cập nhật {updated_questions} câu"
        if created_conversations > 0:
            message += f", tạo {created_conversations} conversations"
        
        return {
            "success": len(errors) == 0,
            "message": message,
            "created_questions": created_questions,
            "updated_questions": updated_questions,
            "created_conversations": created_conversations,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"Error importing bilingual JSON: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Error importing bilingual JSON: {str(e)}",
            "created_questions": 0,
            "updated_questions": 0,
            "errors": [str(e)]
        }


def _parse_transcript_lines(transcript: str, transcript_vi: str) -> list:
    """Parse transcript text into structured lines with speaker labels."""
    lines = []
    
    en_lines = transcript.strip().split("\n") if transcript else []
    vi_lines = transcript_vi.strip().split("\n") if transcript_vi else []
    
    for i, en_line in enumerate(en_lines):
        en_line = en_line.strip()
        if not en_line:
            continue
        
        speaker = ""
        text = en_line
        if ":" in en_line[:5]:
            parts = en_line.split(":", 1)
            speaker = parts[0].strip()
            text = parts[1].strip() if len(parts) > 1 else ""
        
        vi_text = ""
        if i < len(vi_lines):
            vi_line = vi_lines[i].strip()
            if ":" in vi_line[:5]:
                vi_text = vi_line.split(":", 1)[1].strip() if ":" in vi_line else vi_line
            else:
                vi_text = vi_line
        
        lines.append({
            "speaker": speaker,
            "text": text,
            "text_vi": vi_text,
        })
    
    return lines
