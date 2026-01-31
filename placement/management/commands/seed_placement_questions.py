# placement/management/commands/seed_placement_questions.py

import random
from django.core.management.base import BaseCommand
from placement.models import PlacementQuestion, SkillCategory, DifficultyLevel


class Command(BaseCommand):
    help = 'Seed placement questions for the adaptive test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of questions to generate (default: 100)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing questions before seeding'
        )

    def handle(self, *args, **options):
        if options['clear']:
            PlacementQuestion.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all existing placement questions'))

        count = options['count']
        questions_per_skill = count // 9  # 9 skills
        
        created = 0
        
        for skill in SkillCategory:
            for difficulty in DifficultyLevel:
                # Create questions for each skill-difficulty combination
                num_questions = questions_per_skill // 6  # 6 difficulty levels
                if num_questions < 1:
                    num_questions = 1
                
                for i in range(num_questions):
                    question = self._create_question(skill.value, difficulty.value, i)
                    PlacementQuestion.objects.create(**question)
                    created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created} placement questions')
        )

    def _create_question(self, skill: str, difficulty: int, index: int) -> dict:
        """Generate a sample question based on skill and difficulty"""
        
        # IRT parameters based on difficulty
        irt_difficulty = self._difficulty_to_irt(difficulty)
        irt_discrimination = random.uniform(0.8, 1.5)
        irt_guessing = 0.25 if skill not in ['L2'] else 0.33  # Part 2 has 3 options
        
        # Generate question based on skill
        if skill.startswith('L'):
            return self._create_listening_question(skill, difficulty, index, irt_difficulty, irt_discrimination, irt_guessing)
        elif skill.startswith('R'):
            return self._create_reading_question(skill, difficulty, index, irt_difficulty, irt_discrimination, irt_guessing)
        elif skill == 'VOC':
            return self._create_vocabulary_question(difficulty, index, irt_difficulty, irt_discrimination, irt_guessing)
        else:  # GRM
            return self._create_grammar_question(difficulty, index, irt_difficulty, irt_discrimination, irt_guessing)

    def _difficulty_to_irt(self, difficulty: int) -> float:
        """Convert difficulty level to IRT difficulty parameter"""
        mapping = {
            1: -2.0,  # Beginner
            2: -1.0,  # Elementary
            3: 0.0,   # Intermediate
            4: 0.8,   # Upper Intermediate
            5: 1.5,   # Advanced
            6: 2.2,   # Expert
        }
        base = mapping.get(difficulty, 0)
        return base + random.uniform(-0.3, 0.3)

    def _create_listening_question(self, skill, difficulty, index, irt_diff, irt_disc, irt_guess):
        """Create listening questions (L1-L4)"""
        skill_templates = {
            'L1': {  # Photos
                'question': f'Look at the picture and select the statement that best describes what you see.',
                'context': f'[Image showing office scene {index + 1}]',
            },
            'L2': {  # Question Response
                'question': f'Where is the meeting scheduled?',
                'context': '',
            },
            'L3': {  # Conversations
                'question': f'What does the man suggest?',
                'context': f'Man: I think we should postpone the meeting.\nWoman: That might be a good idea. When do you suggest?',
            },
            'L4': {  # Talks
                'question': f'What is the main purpose of this announcement?',
                'context': f'Attention all passengers. Flight 302 to Tokyo has been delayed due to weather conditions.',
            },
        }
        
        template = skill_templates.get(skill, skill_templates['L1'])
        options = self._generate_options(skill, difficulty)
        
        return {
            'skill': skill,
            'difficulty': difficulty,
            'question_text': template['question'],
            'context_text': template['context'],
            'option_a': options[0],
            'option_b': options[1],
            'option_c': options[2],
            'option_d': options[3] if skill != 'L2' else '',
            'correct_answer': random.choice(['A', 'B', 'C'] if skill == 'L2' else ['A', 'B', 'C', 'D']),
            'explanation': f'This is a sample {SkillCategory(skill).label} question at difficulty level {difficulty}.',
            'irt_difficulty': irt_diff,
            'irt_discrimination': irt_disc,
            'irt_guessing': irt_guess,
        }

    def _create_reading_question(self, skill, difficulty, index, irt_diff, irt_disc, irt_guess):
        """Create reading questions (R5-R7)"""
        skill_templates = {
            'R5': {  # Incomplete Sentences
                'question': f'The project deadline has been _______ to next Friday.',
                'context': '',
            },
            'R6': {  # Text Completion
                'question': f'Which word or phrase best fits in blank (1)?',
                'context': f'Dear Mr. Smith,\n\nThank you for your (1)_______ in our services. We are pleased to (2)_______ you that your application has been approved.',
            },
            'R7': {  # Reading Comprehension
                'question': f'What is the main purpose of this email?',
                'context': f'Subject: Annual Review\n\nDear Team,\n\nPlease be reminded that annual performance reviews will take place next week. All employees should prepare their self-assessments by Friday.',
            },
        }
        
        template = skill_templates.get(skill, skill_templates['R5'])
        options = self._generate_options(skill, difficulty)
        
        return {
            'skill': skill,
            'difficulty': difficulty,
            'question_text': template['question'],
            'context_text': template['context'],
            'option_a': options[0],
            'option_b': options[1],
            'option_c': options[2],
            'option_d': options[3],
            'correct_answer': random.choice(['A', 'B', 'C', 'D']),
            'explanation': f'This is a sample {SkillCategory(skill).label} question at difficulty level {difficulty}.',
            'irt_difficulty': irt_diff,
            'irt_discrimination': irt_disc,
            'irt_guessing': irt_guess,
        }

    def _create_vocabulary_question(self, difficulty, index, irt_diff, irt_disc, irt_guess):
        """Create vocabulary questions"""
        vocab_words = [
            ('accommodate', 'to provide lodging or room for'),
            ('implement', 'to put into effect'),
            ('substantial', 'of considerable importance or size'),
            ('comprehensive', 'including all or nearly all elements'),
            ('consecutive', 'following each other continuously'),
        ]
        word, definition = random.choice(vocab_words)
        
        return {
            'skill': 'VOC',
            'difficulty': difficulty,
            'question_text': f'What is the meaning of the word "{word}"?',
            'context_text': '',
            'option_a': definition,
            'option_b': 'to make something smaller',
            'option_c': 'to reject or refuse',
            'option_d': 'to delay or postpone',
            'correct_answer': 'A',
            'explanation': f'"{word}" means "{definition}"',
            'irt_difficulty': irt_diff,
            'irt_discrimination': irt_disc,
            'irt_guessing': irt_guess,
        }

    def _create_grammar_question(self, difficulty, index, irt_diff, irt_disc, irt_guess):
        """Create grammar questions"""
        grammar_questions = [
            ('She _______ to the office every day.', 'goes', 'go', 'going', 'gone'),
            ('The report _______ yesterday.', 'was submitted', 'submitted', 'submit', 'is submitted'),
            ('If I _______ earlier, I would have caught the train.', 'had left', 'left', 'leave', 'leaving'),
        ]
        q, a, b, c, d = random.choice(grammar_questions)
        
        return {
            'skill': 'GRM',
            'difficulty': difficulty,
            'question_text': q,
            'context_text': '',
            'option_a': a,
            'option_b': b,
            'option_c': c,
            'option_d': d,
            'correct_answer': 'A',
            'explanation': f'The correct answer is "{a}" based on grammar rules.',
            'irt_difficulty': irt_diff,
            'irt_discrimination': irt_disc,
            'irt_guessing': irt_guess,
        }

    def _generate_options(self, skill, difficulty):
        """Generate generic options"""
        option_sets = {
            'L1': ['People are sitting in a meeting room', 'A woman is using a computer', 'Documents are on the desk', 'The office is empty'],
            'L2': ['In the conference room at 3 PM', 'I prefer the larger one', 'Yes, I will attend'],
            'L3': ['To reschedule the meeting', 'To hire more staff', 'To reduce the budget', 'To cancel the project'],
            'L4': ['To announce a delay', 'To welcome passengers', 'To provide safety instructions', 'To advertise a service'],
            'R5': ['extended', 'extending', 'extent', 'extension'],
            'R6': ['interest', 'interesting', 'interested', 'interests'],
            'R7': ['To schedule reviews', 'To announce promotions', 'To request time off', 'To introduce a new policy'],
        }
        return option_sets.get(skill, ['Option A', 'Option B', 'Option C', 'Option D'])
