from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_delete, m2m_changed
from django.dispatch import receiver

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    common = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}: {self.description}"


class Word(models.Model):
    category = models.ManyToManyField(Category, related_name='words')
    word = models.CharField(max_length=50, unique=True)
    translation = models.CharField(max_length=50, null=False, blank=False)
    transcription = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return f"{self.word} - {self.translation} - {self.transcription}\n{self.category}"


@receiver(m2m_changed, sender=Word.category.through)
def delete_words_without_categories(sender, instance, action, **kwargs):
    if action in ['post_remove', 'post_clear']:
        if not instance.category.exists():
            instance.delete()

@receiver(pre_delete, sender=Category)
def on_category_delete(sender, instance, **kwargs):
    words = Word.objects.filter(category=instance)
    for word in words:
        if word.category.count() <= 1:
            word.delete()


class Session(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)


class Answer_Attempt(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class Word_Repetiotion(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    next_review = models.DateTimeField()
    repetition_count = models.PositiveIntegerField(default=1)
    last_interval_minutes = models.PositiveIntegerField(default=30)

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