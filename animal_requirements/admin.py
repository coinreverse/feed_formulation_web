from django.contrib import admin
from .models import AnimalRequirement

@admin.register(AnimalRequirement)
class AnimalRequirementAdmin(admin.ModelAdmin):
    list_display = ('animal_type', 'body_weight', 'daily_gain', 'created_at')
    list_filter = ('animal_type', 'created_at')
    search_fields = ('animal_type',)
    ordering = ('animal_type', 'body_weight')