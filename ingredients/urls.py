from django.urls import path
from . import views

urlpatterns = [
    path('', views.ingredients_list, name='ingredients_list'),
    path('detail/<int:ingredient_id>/', views.ingredient_detail, name='ingredient_detail'),
    path('add/', views.add_ingredient, name='add_ingredient'),
    path('edit/<int:ingredient_id>/', views.edit_ingredient, name='edit_ingredient'),
    path('review/<int:ingredient_id>/', views.review_ingredient, name='review_ingredient'),
    path('api/ingredients/', views.api_ingredients_list, name='api_ingredients_list'),
]