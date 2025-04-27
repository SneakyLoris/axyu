from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from datetime import datetime, timedelta
import random

@login_required
def ultra_simple_dashboard(request):
   
    user = request.user
    
    # общая статистика
    stats = {
        'total_words': random.randint(50, 200),
        'total_quizzes': random.randint(10, 50),
        'success_rate': random.randint(60, 95),
    }
    
    # категории
    categories = {
        'Глаголы': random.randint(10, 40),
        'Существительные': random.randint(10, 40),
        'Прилагательные': random.randint(5, 20),
        'Фразы': random.randint(5, 15),
    }
    
    # рузультат за неделю
    week_dates = [(datetime.now() - timedelta(days=i)).strftime('%d.%m') for i in range(7)]
    week_progress = [
        {'date': date, 'words': random.randint(1, 10), 'quizzes': random.randint(0, 3)}
        for date in week_dates
    ]
    
   
    context = {
        'stats': stats,
        'categories': categories,
        'week_progress': week_progress,
    }
    
   # вот тут гпт
    return render(request, 'progress/ultra_simple.html', context)