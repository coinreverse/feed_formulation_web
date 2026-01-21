from django.urls import path

from . import views

urlpatterns = [
    path("api/results/<int:requirement_id>/", views.formula_result_list, name="formula_result_list"),
    path("results/<int:requirement_id>/", views.formula_results_detailed, name="formula_results_detailed"),  # 不带方案索引的URL（兼容旧格式）
    path("results/<int:requirement_id>/<int:solution_index>/", views.formula_results_detailed, name="formula_results_detailed"),  # 显示详细结果
    path("api/run-ga/<int:requirement_id>/", views.run_ga_and_show_results, name="run_ga_and_show_results"),
    path("ga-optimization/", views.ga_optimization_list, name="ga_optimization_list"),
    path("results/", views.formula_results_list, name="formula_results_list"),
    path("input/<int:requirement_id>/", views.formula_results_page, name="formula_results_page"),  # 显示输入页面
]
