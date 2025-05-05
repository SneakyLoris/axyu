from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete, m2m_changed
from django.dispatch import receiver

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.name}: {self.description}"

    class Meta:
        unique_together = ['name', 'owner']

class Word(models.Model):
    category = models.ManyToManyField(Category, related_name='words')
    word = models.CharField(max_length=50)
    translation = models.CharField(max_length=50, null=False, blank=False)
    transcription = models.CharField(max_length=50, null=False, blank=False)

    class Meta:
        unique_together = ['word', 'translation', 'transcription']

@receiver(m2m_changed, sender=Word.category.through)
def delete_words_without_categories(sender, instance, action, **kwargs):
    if action in ['post_remove', 'post_clear']:
        if not instance.category.exists():
            instance.delete()

@receiver(pre_delete, sender=Category)
def on_category_delete(sender, instance, **kwargs):
    words = Word.objects.filter(category=instance)
    for word in words:
        if word.category.count() == 1 and instance in word.category.all():
            word.delete()
            
class Learning_Session(models.Model):
    class Method(models.TextChoices):
        NEW_WORDS = "new_words", "New Words",
        REPEAT = "repeat", "Repeat"
        TEST = "test", "Test"

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=False, default=-1)
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.NEW_WORDS,
        null=False
    )
    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE)

class Answer_Attempt(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    session = models.ForeignKey(Learning_Session, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class Word_Repetition(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    next_review = models.DateTimeField(default=datetime.now() + timedelta(seconds=30))
    repetition_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['user', 'word']


class Learning_Category(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'category']


class Learned_Word(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['user', 'word']

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name} ({self.email})"