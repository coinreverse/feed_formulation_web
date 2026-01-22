# ingredients/translation.py

from modeltranslation.translator import register, TranslationOptions
from ingredients.models import Ingredient, IngredientNutrient, CustomIngredientNutrient

@register(Ingredient)
class IngredientTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

@register(CustomIngredientNutrient)
class CustomIngredientNutrientTranslationOptions(TranslationOptions):
    fields = ('nutrient_name', 'unit')