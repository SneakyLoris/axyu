from rest_framework import serializers
from api import models
from django.contrib.auth.models import User



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category 
        fields = '__all__'

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Word
        fields = '__all__'
    