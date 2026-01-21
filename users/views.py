from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileForm
from django.utils.translation import gettext_lazy as _


def register_view(request):
    """
    用户注册视图
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 登录用户
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            # 使用邮箱进行认证，因为USERNAME_FIELD设置为'email'
            user = authenticate(email=email, password=raw_password)
            if user is not None:  # 确保认证成功
                login(request, user)
                messages.success(request, f"{_('账号')} {email} {_('创建成功！')}")
                return redirect('home')  # 需要定义home URL
            else:
                # 认证失败的情况，可以考虑删除刚创建的用户或采取其他措施
                messages.error(request, f"{_('账户创建后自动登录失败，请尝试手动登录。')}")
                return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'user/register.html', {'form': form})


def login_view(request):
    """
    用户登录视图
    """
    # 检查是否是因为访问受保护页面而被重定向过来的
    if not request.user.is_authenticated and 'next' in request.GET:
        messages.info(request, f"{_('请先登录以访问饲料原料管理功能。')}")

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"{_('欢迎回来,')} {email}!")
                # 登录后重定向到用户原本想访问的页面，或者首页
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, f"{_('用户名或密码不正确。')}")
        else:
            messages.error(request, f"{_('用户名或密码不正确。')}")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'user/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    用户登出视图
    """
    logout(request)
    messages.info(request, f"{_('您已成功退出登录。')}")
    return redirect('home')  # 需要定义home URL


@login_required
def profile_view(request):
    """
    用户个人资料视图
    """
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'user/profile.html', {'form': form})