import json
from django.http import JsonResponse
from django.shortcuts import render
from animal_requirements.models import AnimalRequirement
from formulation.models import FeedFormulaResult
from formulation.services.ga_service import run_ga_and_import
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)


def format_formula_result_data(qs):
    """辅助函数：格式化配方结果数据为JSON响应格式"""
    data = []
    for r in qs:
        # 格式化营养成分数据，保留两位小数
        formatted_ingredients = []
        for i in r.ingredients.all():
            formatted_ingredients.append({
                "name": i.ingredient.name,  # 中文名称
                "ratio": round(i.ratio * 100, 2)  # 转换为百分比并保留两位小数
            })

        # 按照比例从高到低排序
        formatted_ingredients.sort(key=lambda x: x['ratio'], reverse=True)

        data.append({
            "id": r.id,
            "solution_index": r.solution_index,
            "total_cost": round(float(r.total_cost), 2),
            "dm": round(float(r.dm), 2),
            "ca": round(float(r.ca), 2),
            "cp": round(float(r.cp), 2),
            "p": round(float(r.p), 2),
            "ndf": round(float(r.ndf), 2),
            "me": round(float(r.me), 2),
            "mp": round(float(r.mp), 2),
            "ingredients": formatted_ingredients,
            # 添加更多营养成分信息
            "营养成分": {
                "干物质(DM)": f"{round(float(r.dm), 2)}%",
                "钙(Ca)": f"{round(float(r.ca), 2)}%",
                "粗蛋白(CP)": f"{round(float(r.cp), 2)}%",
                "磷(P)": f"{round(float(r.p), 2)}%",
                "中性洗涤纤维(NDF)": f"{round(float(r.ndf), 2)}%",
                "代谢能(ME)": f"{round(float(r.me), 2)}%",
                "代谢蛋白(MP)": f"{round(float(r.mp), 2)}%"
            }
        })

    return data


def formula_result_list(request, requirement_id):
    # 检查动物需求记录是否存在且已通过审核
    try:
        AnimalRequirement.objects.get(id=requirement_id, status=AnimalRequirement.APPROVED)
    except AnimalRequirement.DoesNotExist:
        return JsonResponse(
            {"error": f"动物营养需求记录(ID: {requirement_id})不存在或未通过审核，请先创建并审核相应的记录。"},
            status=404)

    qs = FeedFormulaResult.objects.filter(
        requirement_id=requirement_id
    ).prefetch_related("ingredients", "ingredients__ingredient").order_by("solution_index")  # 按solution_index升序排列

    data = format_formula_result_data(qs)

    # 使用ensure_ascii=False确保中文正常显示
    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response["Content-Type"] = "application/json; charset=utf-8"
    return response


def formula_results_page(request, requirement_id):
    """渲染前端页面 - 显示动物营养需求和原料信息，用于运行遗传算法"""
    # 检查动物需求记录是否存在且已通过审核
    try:
        AnimalRequirement.objects.get(id=requirement_id, status=AnimalRequirement.APPROVED)
    except AnimalRequirement.DoesNotExist:
        return JsonResponse(
            {"error": f"动物营养需求记录(ID: {requirement_id})不存在或未通过审核，请先创建并审核相应的记录。"},
            status=404)

    context = {
        'requirement_id': requirement_id
    }
    return render(request, 'formulation/formula_results.html', context)


def formula_results_detailed(request, requirement_id):
    """渲染前端页面 - 显示详细的配方结果"""
    # 检查动物需求记录是否存在且已通过审核
    try:
        AnimalRequirement.objects.get(id=requirement_id, status=AnimalRequirement.APPROVED)
    except AnimalRequirement.DoesNotExist:
        return JsonResponse(
            {"error": f"动物营养需求记录(ID: {requirement_id})不存在或未通过审核，请先创建并审核相应的记录。"},
            status=404)

    context = {
        'requirement_id': requirement_id
    }
    return render(request, 'formulation/formula_results_detailed.html', context)


@csrf_exempt
def run_ga_and_show_results(request, requirement_id):
    """运行遗传算法并展示结果"""
    try:
        # 检查动物需求记录是否存在且已通过审核
        try:
            requirement = AnimalRequirement.objects.get(id=requirement_id, status=AnimalRequirement.APPROVED)
        except AnimalRequirement.DoesNotExist:
            return JsonResponse({
                "error": f"动物营养需求记录(ID: {requirement_id})不存在或未通过审核，只有已通过审核的需求才能运行遗传算法。"},
                status=404)

        # 获取前端传递的selected_ingredient_ids参数
        selected_ingredient_ids = None
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                selected_ingredient_ids = data.get('selected_ingredient_ids', None)
            except json.JSONDecodeError:
                pass

        # 运行遗传算法并导入结果到数据库，传递selected_ingredient_ids参数
        run_ga_and_import(requirement_id, selected_ingredient_ids)

        # 获取计算后的结果
        qs = FeedFormulaResult.objects.filter(
            requirement_id=requirement_id
        ).prefetch_related("ingredients", "ingredients__ingredient").order_by("solution_index")  # 按solution_index升序排列

        data = format_formula_result_data(qs)

        # 返回JSON响应
        response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
        response["Content-Type"] = "application/json; charset=utf-8"
        return response

    except Exception as e:
        logger.error(f"运行遗传算法时出错: {str(e)}")
        return JsonResponse({"error": f"运行遗传算法时出错: {str(e)}"}, status=500)


def ga_optimization_list(request):
    """遗传算法优化列表页面 - 显示所有已通过审核的动物需求供用户选择进行优化"""
    # 只显示审核状态为"已通过"的动物营养需求
    requirements = AnimalRequirement.objects.filter(status=AnimalRequirement.APPROVED).order_by('-created_at')

    context = {
        'requirements': requirements
    }
    return render(request, 'formulation/ga_optimization_list.html', context)


def formula_results_list(request):
    """配方结果列表页面 - 显示所有已计算的配方结果"""
    # 只显示已通过审核的需求的配方结果
    results = FeedFormulaResult.objects.select_related('requirement').filter(
        requirement__status=AnimalRequirement.APPROVED
    ).order_by('-created_at')

    # 按需求分组结果
    grouped_results = {}
    for result in results:
        req_id = result.requirement.id
        if req_id not in grouped_results:
            grouped_results[req_id] = {
                'requirement': result.requirement,
                'results': []
            }
        grouped_results[req_id]['results'].append(result)

    # 对每个组内的结果按 solution_index 排序
    for group in grouped_results.values():
        group['results'].sort(key=lambda x: x.solution_index)

    context = {
        'grouped_results': grouped_results.values()
    }
    return render(request, 'formulation/formula_results_list.html', context)