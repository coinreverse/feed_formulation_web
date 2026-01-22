from feed_formulation_web.models import DailyVisit
from formulation.models import FeedFormulaResult
from ingredients.models import Ingredient
from users.models import CustomUser
from django.shortcuts import render
from datetime import datetime, timedelta
import random


# 主页视图，包含统计数据和图表
def home(request):
    # 统计数据
    formula_count = FeedFormulaResult.objects.count()
    ingredient_count = Ingredient.objects.count()
    user_count = CustomUser.objects.count()

    # 如果没有真实数据，使用模拟数据
    if formula_count == 0:
        formula_count = random.randint(50, 200)
    if ingredient_count == 0:
        ingredient_count = random.randint(30, 100)
    if user_count == 0:
        user_count = random.randint(10, 50)

    # 生成最近7天配方生成趋势数据（符合模板期望的{date, count}对象列表）
    formula_trend = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        # 尝试获取真实数据，如果没有则使用模拟数据
        real_count = FeedFormulaResult.objects.filter(created_at__date=datetime.strptime(date, '%Y-%m-%d')).count()
        if real_count > 0:
            count = real_count
        else:
            count = random.randint(0, 15)
        formula_trend.append({'date': date, 'count': count})

    # 生成最近30天访问量趋势数据
    access_trend = []
    for i in range(29, -1, -1):
        date = (datetime.now() - timedelta(days=i)).date()
        # 尝试获取真实访问量数据
        visit = DailyVisit.objects.filter(visit_date=date).first()
        if visit:
            count = visit.count
        else:
            count = 0  # 没有记录时显示0
        access_trend.append({'date': date.strftime('%Y-%m-%d'), 'count': count})

    context = {
        'formula_count': formula_count,
        'ingredient_count': ingredient_count,
        'user_count': user_count,
        'formula_trend': formula_trend,
        'access_trend': access_trend
    }

    return render(request, 'home.html', context)