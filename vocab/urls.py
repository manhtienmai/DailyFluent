from django.urls import path
from . import views

app_name = 'vocab'

urlpatterns = [
    # Sets CRUD
    path('sets/', views.SetListView.as_view(), name='set_list'),
    path('sets/create/', views.SetCreateView.as_view(), name='set_create'),
    path('sets/<int:pk>/', views.SetDetailView.as_view(), name='set_detail'),
    path('sets/<int:pk>/study/', views.SetStudyView.as_view(), name='set_study'),
    path('sets/<int:pk>/edit/', views.SetUpdateView.as_view(), name='set_update'),
    path('sets/<int:pk>/delete/', views.SetDeleteView.as_view(), name='set_delete'),

    # APIs
    path('api/search/', views.search_words_api, name='api_search'),
    path('api/sets/<int:set_id>/add/', views.add_item_api, name='api_add_item'),
    path('api/sets/<int:set_id>/remove/', views.remove_item_api, name='api_remove_item'),
    path('sets/<int:pk>/import/', views.import_json_view, name='set_import'),

    # Lists
    path('', views.EnglishListView.as_view(), name='list'),
    path('english/', views.EnglishListView.as_view(), name='english_list'),
    path('english/<str:word>/', views.VocabularyDetailView.as_view(), name='vocabulary_detail'),
    path('games/', views.GamesView.as_view(), name='games'),

    path('progress/', views.ProgressView.as_view(), name='progress'),
    path('study-status/', views.StudyStatusView.as_view(), name='study_status'),
    path('typing/', views.TypingView.as_view(), name='typing'),
    path('phrases/', views.PhraseListView.as_view(), name='phrases'),
    path('my-words/', views.MyWordsView.as_view(), name='my_words'),

    # TOEIC/Course pages
    path('courses/', views.CourseListView.as_view(), name='course_list'), # Alias/New home
    path('toeic/', views.CourseListView.as_view(), name='toeic_home'), # Legacy redirect/alias
    
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<slug:slug>/set/<int:set_number>/', views.CourseSetDetailView.as_view(), name='course_set_detail'),
    path('courses/<slug:slug>/set/<int:set_number>/learn/', views.CourseLearnView.as_view(), name='course_learn'),
    
    # Quiz view
    path('courses/<slug:slug>/set/<int:set_number>/quiz/', views.CourseQuizView.as_view(), name='course_quiz'), 
    
    path('toeic/review/', views.ToeicReviewView.as_view(), name='toeic_review'),

    # Games (Placeholders)
    path('games/mcq/', views.GameMCQView.as_view(), name='game_mcq'),
    path('games/matching/', views.GameMatchingView.as_view(), name='game_matching'),
    path('games/listening/', views.GameListeningView.as_view(), name='game_listening'),
    path('games/fill/', views.GameFillView.as_view(), name='game_fill'),
    path('games/dictation/', views.GameDictationView.as_view(), name='game_dictation'),

    # TOEIC APIs
    path('api/toeic/learn-result/', views.api_toeic_learn_result, name='api_toeic_learn_result'),
    path('api/toeic/quiz-result/', views.api_toeic_quiz_result, name='api_toeic_quiz_result'),
    path('api/toeic/review-grade/', views.api_toeic_review_grade, name='api_toeic_review_grade'),
    
    # Flashcard APIs (unified)
    path('api/flashcard/grade/', views.api_flashcard_grade_english, name='flashcard_grade_english'),
    
    # Game APIs
    path('api/games/buy-life/', views.api_buy_game_life, name='api_buy_game_life'),
]
