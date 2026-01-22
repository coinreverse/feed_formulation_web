# animal_requirements/translation.py

from modeltranslation.translator import register, TranslationOptions
from animal_requirements.models import AnimalRequirement, CustomNutrientRequirement

@register(AnimalRequirement)
class AnimalRequirementTranslationOptions(TranslationOptions):
    fields = ('animal_type',)

@register(CustomNutrientRequirement)
class CustomNutrientRequirementTranslationOptions(TranslationOptions):
    fields = ('nutrient_name', 'unit')
