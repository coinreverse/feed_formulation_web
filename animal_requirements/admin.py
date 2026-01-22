from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import AnimalRequirement, CustomNutrientRequirement

@admin.register(AnimalRequirement)
class AnimalRequirementAdmin(TranslationAdmin):
    list_display = ('animal_type', 'body_weight', 'daily_gain', 'created_at')
    list_filter = ('animal_type', 'created_at')
    search_fields = ('animal_type',)
    ordering = ('animal_type', 'body_weight')


@admin.register(CustomNutrientRequirement)
class CustomNutrientRequirementAdmin(TranslationAdmin):
    list_display = ('nutrient_name', 'nutrient_lower', 'nutrient_upper', 'unit', 'requirement')
    list_filter = ('requirement',)
    search_fields = ('nutrient_name',)