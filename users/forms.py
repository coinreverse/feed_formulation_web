from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, EmailVerificationCode
from django.utils.translation import gettext_lazy as _


class CustomUserCreationForm(UserCreationForm):
    """
    自定义用户注册表单
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入邮箱地址')
        })
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入用户名')
        })
    )

    password1 = forms.CharField(
        label=_("密码"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入密码')
        }),
    )

    password2 = forms.CharField(
        label=_("确认密码"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('请再次输入密码')
        }),
        strip=False,
    )

    # 添加验证码字段
    verification_code = forms.CharField(
        label=_('验证码'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入验证码')
        }),
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")

    def clean_verification_code(self):
        email = self.cleaned_data.get('email')
        code = self.cleaned_data.get('verification_code')

        if not email or not code:
            raise forms.ValidationError(_('请填写邮箱和验证码'))

        try:
            verification_code = EmailVerificationCode.objects.filter(
                email=email,
                code=code,
                is_used=False
            ).latest('created_at')

            if not verification_code.is_valid():
                raise forms.ValidationError(_('验证码已过期或无效'))

        except EmailVerificationCode.DoesNotExist:
            raise forms.ValidationError(_('验证码不正确'))

        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            # 标记验证码为已使用
            email = self.cleaned_data.get('email')
            code = self.cleaned_data.get('verification_code')
            verification_code = EmailVerificationCode.objects.filter(
                email=email, code=code
            ).latest('created_at')
            verification_code.is_used = True
            verification_code.save()

        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    自定义用户登录表单
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入邮箱地址')
        })
    )

    password = forms.CharField(
        label=_(),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入密码')
        }),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'language']


# 添加密码重置请求表单
class PasswordResetRequestForm(forms.Form):
    """
    密码重置请求表单
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入您的邮箱地址')
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('该邮箱未注册'))
        return email


# 添加密码重置表单
class PasswordResetForm(forms.Form):
    """
    密码重置表单
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    verification_code = forms.CharField(
        label=_('验证码'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入验证码')
        }),
        required=True
    )
    new_password1 = forms.CharField(
        label=_("新密码"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入新密码')
        }),
    )
    new_password2 = forms.CharField(
        label=_("确认新密码"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('请再次输入新密码')
        }),
        strip=False,
    )

    def clean_verification_code(self):
        email = self.cleaned_data.get('email')
        code = self.cleaned_data.get('verification_code')

        if not email or not code:
            raise forms.ValidationError(_('请填写邮箱和验证码'))

        try:
            verification_code = EmailVerificationCode.objects.filter(
                email=email,
                code=code,
                is_used=False
            ).latest('created_at')

            if not verification_code.is_valid():
                raise forms.ValidationError(_('验证码已过期或无效'))

        except EmailVerificationCode.DoesNotExist:
            raise forms.ValidationError(_('验证码不正确'))

        return code

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("两次输入的密码不一致"))
