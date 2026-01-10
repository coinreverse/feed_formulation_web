from django.db import models
from django.contrib.auth.models import AbstractUser

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
