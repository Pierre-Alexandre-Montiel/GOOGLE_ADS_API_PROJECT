from django.db import models
from django.contrib import auth
from django import forms  
from django.contrib.auth.models import User  
from django.contrib.auth.forms import UserCreationForm  
from django.core.exceptions import ValidationError  
from django.forms.forms import Form

class Post(models.Model):
    campaign_name = models.CharField(max_length=64)
    campaign_type = models.CharField(max_length=64)
    date = models.CharField(max_length=64)
    budget = models.CharField(max_length=64)
    status = models.CharField(max_length=64)
    biding_strategy = models.CharField(max_length=64)
    spending = models.CharField(max_length=64)
    targeting = models.CharField(max_length=64)

class CustomUserCreationForm(UserCreationForm):  
    username = forms.CharField(label='username')  
    password1 = forms.CharField(label='password', widget=forms.PasswordInput)  
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)  
  
    def username_clean(self):  
        username = self.cleaned_data['username'].lower()  
        new = User.objects.filter(username = username)  
        if new.count():  
            raise ValidationError("User Already Exist")  
        return username  
  
    def clean_password2(self):  
        password1 = self.cleaned_data['password1']  
        password2 = self.cleaned_data['password2']  
  
        if password1 and password2 and password1 != password2:  
            raise ValidationError("Password don't match")  
        return password2  
  
    def save(self, commit = True):  
        user = User.objects.create_user(  
            self.cleaned_data['username'], None,
            self.cleaned_data['password1']  
        )
        return user