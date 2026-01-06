from django.urls import path
from . import views

urlpatterns = [
    path('', views.animal_requirements_list, name='animal_requirements_list'),
    path('add/', views.add_animal_requirement, name='add_animal_requirement'),
    path('edit/<int:requirement_id>/', views.edit_animal_requirement, name='edit_animal_requirement'),
    path('<int:requirement_id>/review/', views.review_animal_requirement, name='review_animal_requirement'),
    path('<int:requirement_id>/', views.animal_requirement_detail, name='animal_requirement_detail'),
    path('api/requirements/<int:requirement_id>/', views.api_animal_requirement, name='api_animal_requirement'),
]