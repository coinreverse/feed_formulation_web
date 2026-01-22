from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    """
    自定义用户模型
    """
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'  # 使用邮箱作为登录字段
    REQUIRED_FIELDS = ['username']  # 创建超级用户时需要的字段

    LANGUAGE_CHOICES = [
        ('zh-hans', '中文'),
        ('en', 'English'),
    ]
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='zh-hans')

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'


class EmailVerificationCode(models.Model):
    """
    邮箱验证码模型
    """
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"{self.email} - {self.code} ({'已使用' if self.is_used else '未使用'})"

    class Meta:
        verbose_name = '邮箱验证码'
        verbose_name_plural = '邮箱验证码'

    def save(self, *args, **kwargs):
        # 设置默认过期时间为5分钟后
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_valid(self):
        """
        检查验证码是否有效
        """
        return not self.is_used and timezone.now() < self.expires_at