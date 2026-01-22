from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Ingredient, IngredientNutrient, CustomIngredientNutrient

@admin.register(Ingredient)
class IngredientAdmin(TranslationAdmin):
    list_display = ('name', 'cost', 'status', 'created_at', 'created_by', 'approved_by', 'approved_at')
    search_fields = ('name',)
    list_filter = ('status', 'created_at', 'created_by')

@admin.register(IngredientNutrient)
class IngredientNutrientAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'dm', 'calcium', 'protein', 'phosphorus', 'ndf', 'metabolizable_energy', 'mp')
    search_fields = ('ingredient__name',)

@admin.register(CustomIngredientNutrient)
class CustomIngredientNutrientAdmin(TranslationAdmin):
    list_display = ('ingredient', 'nutrient_name', 'value', 'unit')
    search_fields = ('ingredient__name', 'nutrient_name')