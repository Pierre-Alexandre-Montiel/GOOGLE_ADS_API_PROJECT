from django import forms
from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Post
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect

class LogForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UpdateUser(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()
    email = forms.EmailField()
    description = forms.CharField(widget=forms.Textarea)
    picture = forms.FileField()

class PostForm(forms.ModelForm):
    class Meta:
        model= Post
        fields = ["campaign_name", "campaign_type", "date", "budget", "status", "biding_strategy", "spending", "targeting"] 
        widgets = {
            'date': forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control', 
               'placeholder': 'Select a date',
               'type': 'date'
        }),
    }

    