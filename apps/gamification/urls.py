"""URLs de gamification: Quiz, Tips, Rewards, Badges, Class Mode, Quick Quiz."""
from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # === QUIZ ===
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('quiz/create/', views.quiz_create, name='quiz_create'),
    path('quiz/rapido/', views.quick_quiz_create, name='quick_quiz_create'),
    path('quiz/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:pk>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quiz/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),
    path('quiz/<int:pk>/attempt/', views.quiz_attempt, name='quiz_attempt'),
    path('quiz/<int:pk>/results/', views.quiz_results, name='quiz_results'),

    # === TIPS (+XP manual) ===
    path('tips/', views.tip_list, name='tip_list'),
    path('tips/create/', views.tip_create, name='tip_create'),

    # === REWARDS STORE ===
    path('rewards/', views.reward_list, name='reward_list'),
    path('rewards/create/', views.reward_create, name='reward_create'),
    path('rewards/<int:pk>/redeem/', views.reward_redeem, name='reward_redeem'),

    # === BADGES ===
    path('badges/', views.badge_list, name='badge_list'),
    path('badges/create/', views.badge_create, name='badge_create'),
    path('badges/<int:pk>/award/', views.badge_award, name='badge_award'),

    # === MODO CLASE / PRESENTACIÓN ===
    path('presentacion/<int:course_pk>/', views.presentation_mode, name='presentation_mode'),
]