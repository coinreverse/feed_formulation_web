from django.db import models
from datetime import date


class DailyVisit(models.Model):
    visit_date = models.DateField(default=date.today, unique=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-visit_date']
        app_label = 'feed_formulation_web'  # 添加这一行

    def __str__(self):
        return f"{self.visit_date} - {self.count} 次访问"