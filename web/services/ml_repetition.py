from random import random
from threading import Thread

from django.db import close_old_connections
from django.utils import timezone
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from web.models import Answer_Attempt, Word_Repetition


DEFAULT_INTERVALS = [30, 120, 360, 1440, 4320]  # 30мин, 2ч, 6ч, 1д, 3д

class RepetitionMLService:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=30)
        self.is_trained = False
        self.training_lock = False

    def get_initial_interval(self):
        return DEFAULT_INTERVALS[0]
    
    def _get_features(self, user, word):
        attempts = Answer_Attempt.objects.filter(
            user=user, 
            word=word
        ).order_by('-timestamp')[:5]
        
        return {
            'attempts_count': attempts.count(),
            'last_correct': int(attempts[0].is_correct) if attempts else 0,
            'success_rate': sum(a.is_correct for a in attempts)/len(attempts) if attempts else 0,
            'word_len': len(word.word),
            'time_since_last': (timezone.now() - attempts[0].timestamp).total_seconds() if attempts else 0,
        }
    
    def _train_thread(self, user):
        try:
            self.training_lock = True
            close_old_connections()
            
            attempts = Answer_Attempt.objects.filter(user=user)
            if len(attempts) < 20:
                return
            
            X, y = [], []
            for attempt in attempts:
                features = self._get_features(user, attempt.word)
                X.append(list(features.values()))
                y.append(int(attempt.is_correct))
            
            self.model.fit(X, y)
            self.is_trained = True
        finally:
            self.training_lock = False
    
    def train_for_user_async(self, user):
        if not self.training_lock and random.random() < 0.3:
            thread = Thread(target=self._train_thread, args=(user,))
            thread.daemon = True
            thread.start()
    
    def predict_next_interval(self, user, word, current_repetition):
        base_interval = DEFAULT_INTERVALS[min(current_repetition, len(DEFAULT_INTERVALS)-1)]
        
        if not self.is_trained:
            return base_interval
        
        try:
            features = self._get_features(user, word)
            proba = self.model.predict_proba([list(features.values())])[0][1]
            
            if proba > 0.9:  # Очень легко
                return base_interval * 2
            elif proba > 0.7:
                return base_interval * 1.5
            elif proba > 0.5:
                return base_interval
            else:  # Сложно
                return max(30, base_interval * 0.7)  # Не меньше 30 минут
        except:
            return base_interval


ml_service = RepetitionMLService()