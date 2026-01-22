from django.utils import timezone
from .models import DailyVisit


class VisitTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 只统计首页访问
        if request.path == '/':
            today = timezone.now().date()
            visit, created = DailyVisit.objects.get_or_create(visit_date=today)
            visit.count += 1
            visit.save()

        response = self.get_response(request)
        return response