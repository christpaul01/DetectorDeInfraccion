from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)
    gender = models.CharField(
        max_length=6,
        choices = [('MALE', 'MALE'),('FEMALE', 'FEMALE')])

    def __str__(self):
        return self.user.username


