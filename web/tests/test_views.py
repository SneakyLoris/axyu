from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser
from api.models import Category, Word, Learned_Word, Word_Repetition, Learning_Category, Feedback
from web.forms import AddWordForm, RegistrationForm, AuthForm, FeedbackForm
import os
import json

from django.contrib.messages import get_messages
from django.contrib import messages
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

User = get_user_model()

class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('registration')
        self.valid_data = {
            'username': 'testuser',
            'password': '123',
            'password2': '123',
            'email': 'test@test.ru'
        }
    
    def test_get_request(self):
        """Тест отображения формы при GET-запросе"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/registration.html')
        self.assertIsInstance(response.context['form'], RegistrationForm)
        self.assertFalse(response.context['is_success'])
    
    def test_valid_post_request(self):
        """Тест успешной регистрации при валидных данных"""
        response = self.client.post(self.url, data=self.valid_data)
        
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@test.ru')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_success'])
        self.assertTrue(user.check_password('123'))

    def test_invalid_post_request(self):
        """Тест с невалидными данными формы"""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'wrongpassword'
        
        response = self.client.post(self.url, data=invalid_data)
        
        self.assertFalse(User.objects.filter(username='testuser').exists())
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_success'])
        self.assertTrue(response.context['form'].errors)

    def test_existing_username(self):
        """Тест попытки регистрации с существующим именем пользователя"""
        User.objects.create_user(username='testuser', password='123')
        
        response = self.client.post(self.url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_success'])
        self.assertIn('username', response.context['form'].errors)

    def test_existing_email(self):
        """Тест попытки регистрации с существующим email"""
        User.objects.create_user(
            username='existinguser',
            email='test@test.ru',
            password='123'
        )
        
        response = self.client.post(self.url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_success'])
        self.assertIn('email', response.context['form'].errors)

def test_missing_fields(self):
    """Тест с отсутствующими обязательными полями"""
    required_fields = ['username', 'email', 'password', 'password2']
    
    for field in required_fields:
        with self.subTest(field=field):
            incomplete_data = self.valid_data.copy()
            del incomplete_data[field]
            
            response = self.client.post(self.url, data=incomplete_data)
            
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['is_success'])
            self.assertIn(field, response.context['form'].errors)
        
            error_msg = str(response.context['form'].errors[field])
            self.assertIn('обязател', error_msg.lower())


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )

    def test_get_request(self):
        """Тест отображения формы при GET-запросе"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/auth.html')
        self.assertContains(response, 'form')

    def test_successful_login(self):
        """Тест успешной аутентификации"""
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': '123'
        }, follow=True)
        
        self.assertRedirects(response, reverse('main'))
        self.assertTrue(response.context['user'].is_authenticated)

    def test_wrong_credentials(self):
        """Тест с неверными учетными данными"""
        response = self.client.post(self.url, {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertEqual(
            response.context['form'].errors['__all__'][0],
            "Введены неверные данные"
        )

    def test_empty_credentials(self):
        """Тест с пустыми полями"""
        for field in ['username', 'password']:
            with self.subTest(field=field):
                invalid_data = {
                    'username': 'testuser',
                    'password': '123'
                }
                invalid_data[field] = ''
                
                response = self.client.post(self.url, invalid_data)
                
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context['user'].is_authenticated)
                self.assertIn(field, response.context['form'].errors)

    def test_inactive_user(self):
        """Тест с неактивным пользователем"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': '123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertEqual(
            response.context['form'].errors['__all__'][0],
            "Введены неверные данные"
        )


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('logout') 
        self.user = User.objects.create_user(
            username='testuser',
            password='123'
        )

    def test_logout_authenticated_user(self):
        """Тест выхода авторизованного пользователя"""
        # Логиним пользователя
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('main'))
        response = self.client.get(reverse('main'))
        self.assertTrue(isinstance(response.context['user'], AnonymousUser))

    def test_logout_unauthenticated_user(self):
        """Тест выхода неавторизованного пользователя"""
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('main'))
        response = self.client.get(reverse('main'))
        self.assertTrue(isinstance(response.context['user'], AnonymousUser))

    def test_post_request(self):
        """Тест POST-запроса"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('main'))


class LearningViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('learning')

    def test_learning_view_get(self):
        """Тест GET-запроса для learning_view"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_learning_view_authenticated(self):
        """Тест для авторизованного пользователя"""
        User = get_user_model()
        User.objects.create_user(username='testuser', password='123')
        self.client.login(username='testuser', password='123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/learning.html')
        self.assertIsNotNone(response.context)


class LearningNewWordsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('learning_new_words')  # Проверьте имя URL

    def test_learning_view_get(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_access(self):
        User = get_user_model()
        User.objects.create_user(username='testuser', password='123')
        self.client.login(username='testuser', password='123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/new_words.html')
        self.assertIsNotNone(response.context)


class LearningRepeatViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('learning_repeat')

    def test_repeat_view_response(self):
        """Тест ответа repeat_view"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_access(self):
        """Тест доступа для авторизованных пользователей"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.create_user(username='testuser', password='123')
        self.client.login(username='testuser', password='123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    
class LearningTestsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('learning_tests')
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        
        self.public_category = Category.objects.create(
            name='Public Category',
            description='Public description',
            owner=None
        )
        self.user_category = Category.objects.create(
            name='User Category',
            description='User description',
            owner=self.user
        )
        self.other_user_category = Category.objects.create(
            name='Other User Category',
            description='Other description',
            owner=User.objects.create_user(username='other', password='otherpass')
        )

    def test_unauthenticated_access(self):
        """Тест доступа для неавторизованного пользователя"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_access(self):
        """Тест для авторизованного пользователя"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/select_test.html')

    def test_categories_context(self):
        """Тест контекста с категориями"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertIn('categories', response.context)
        self.assertIn('user_selected_categories', response.context)
        
        self.assertEqual(len(response.context['categories']), 2)
        
        category_ids = [c.id for c in response.context['categories']]
        self.assertIn(self.public_category.id, category_ids)
        self.assertIn(self.user_category.id, category_ids)
        self.assertNotIn(self.other_user_category.id, category_ids)

    def test_only_public_categories_for_new_user(self):
        """Тест для нового пользователя без своих категорий"""
        User.objects.create_user(username='newuser', password='456')
        self.client.login(username='newuser', password='456')
        
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.context['categories']), 1)
        self.assertEqual(response.context['categories'][0].id, self.public_category.id)
        self.assertEqual(len(response.context['user_selected_categories']), 0)

    def test_user_selected_categories(self):
        """Тест выбранных пользователем категорий"""
        self.client.login(username='testuser', password='123')
        
        Learning_Category.objects.create(
            user=self.user,
            category=self.public_category
        )
        
        response = self.client.get(self.url)
        
        self.assertIn('user_selected_categories', response.context)
        self.assertEqual(len(response.context['user_selected_categories']), 1)
        self.assertIn(self.public_category.id, response.context['user_selected_categories'])

    def test_no_selected_categories(self):
        """Тест когда пользователь не выбрал ни одной категории"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.context['user_selected_categories']), 0)

    def test_multiple_selected_categories(self):
        """Тест с несколькими выбранными категориями"""
        self.client.login(username='testuser', password='123')
        
        # Создаем несколько выбранных категорий
        Learning_Category.objects.create(user=self.user, category=self.public_category)
        Learning_Category.objects.create(user=self.user, category=self.user_category)
        
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.context['user_selected_categories']), 2)
        self.assertIn(self.public_category.id, response.context['user_selected_categories'])
        self.assertIn(self.user_category.id, response.context['user_selected_categories'])


class CategoriesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('categories') 
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        
        self.public_category = Category.objects.create(
            name='Public Category',
            description='Public description',
            owner=None
        )
        self.user_category = Category.objects.create(
            name='User Category',
            description='User description',
            owner=self.user
        )
        self.other_user_category = Category.objects.create(
            name='Other User Category',
            description='Other description',
            owner=User.objects.create_user(username='other', password='otherpass')
        )

    def test_unauthenticated_access(self):
        """Тест доступа для неавторизованного пользователя"""
        response = self.client.get(self.url, follow=False)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/categories.html')

        categories = response.context['categories']
        self.assertEqual(categories.count(), 1)
        
        category_ids = [c.id for c in categories]
        self.assertIn(self.public_category.id, category_ids)
        self.assertNotIn(self.user_category.id, category_ids)
        self.assertNotIn(self.other_user_category.id, category_ids)

    def test_authenticated_access(self):
        """Тест для авторизованного пользователя"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/categories.html')

    def test_categories_context(self):
        """Тест контекста с категориями"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertIn('categories', response.context)
        self.assertIn('user_selected_categories', response.context)
        
        categories = response.context['categories']
        self.assertEqual(categories.count(), 2)
        
        category_ids = [c.id for c in categories]
        self.assertIn(self.public_category.id, category_ids)
        self.assertIn(self.user_category.id, category_ids)
        self.assertNotIn(self.other_user_category.id, category_ids)
  
    def test_user_selected_categories(self):
        """Тест выбранных пользователем категорий"""
        self.client.login(username='testuser', password='123')
        
        Learning_Category.objects.create(
            user=self.user,
            category=self.public_category
        )
        
        response = self.client.get(self.url)
        
        selected_categories = response.context['user_selected_categories']
        self.assertEqual(len(selected_categories), 1)
        self.assertIn(self.public_category.id, selected_categories)

    def test_no_selected_categories(self):
        """Тест когда пользователь не выбрал ни одной категории"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.context['user_selected_categories']), 0)

    def test_multiple_selected_categories(self):
        """Тест с несколькими выбранными категориями"""
        self.client.login(username='testuser', password='123')
        
        Learning_Category.objects.create(user=self.user, category=self.public_category)
        Learning_Category.objects.create(user=self.user, category=self.user_category)
        
        response = self.client.get(self.url)
        
        selected_categories = response.context['user_selected_categories']
        self.assertEqual(len(selected_categories), 2)
        self.assertIn(self.public_category.id, selected_categories)
        self.assertIn(self.user_category.id, selected_categories)

    def test_only_public_categories_for_new_user(self):
        """Тест для нового пользователя без своих категорий"""
        User.objects.create_user(username='newuser', password='newpass')
        self.client.login(username='newuser', password='newpass')
        
        response = self.client.get(self.url)
    
        categories = response.context['categories']
        self.assertEqual(categories.count(), 1)
        self.assertEqual(categories[0].id, self.public_category.id)
        self.assertEqual(len(response.context['user_selected_categories']), 0)
  

class CategoryTestViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@example.com'
        )
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            owner=self.user
        )
        self.url = reverse('category_test')  # Убедитесь в правильности имени URL

    def test_unauthenticated_access(self):
        """Тест доступа для неавторизованного пользователя"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_authenticated_access_valid_category(self):
        """Тест с валидной категорией"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(f"{self.url}?category_id={self.category.id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/tests.html')
        self.assertEqual(response.context['category'], self.category)

    def test_authenticated_access_invalid_category(self):
        """Тест с несуществующей категорией"""
        self.client.login(username='testuser', password='123')
        invalid_id = 666666
        response = self.client.get(f"{self.url}?category_id={invalid_id}")
        
        self.assertEqual(response.status_code, 404)

    def test_missing_category_id(self):
        """Тест без параметра category_id"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 404)

    def test_empty_category_id(self):
        """Тест с пустым category_id"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(f"{self.url}?category_id=")
        self.assertEqual(response.status_code, 404)

    def test_invalid_category_id_format(self):
        """Тест с нечисловым category_id"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(f"{self.url}?category_id=abc")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_category(self):
        """Тест с несуществующим category_id"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(f"{self.url}?category_id=9999")
        self.assertEqual(response.status_code, 404)

    def test_category_access_permissions(self):
        """Тест доступа к категории другого пользователя"""
        other_user = User.objects.create_user(username='other', password='otherpass')
        other_category = Category.objects.create(
            name='Other Category',
            description='Other Description',
            owner=other_user
        )
        
        self.client.login(username='testuser', password='123')
        response = self.client.get(f"{self.url}?category_id={other_category.id}")
        
        self.assertEqual(response.status_code, 403)

    def test_invalid_category_id_format(self):
        """Тест с невалидным форматом category_id"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(f"{self.url}?category_id=invalid")
        
        self.assertEqual(response.status_code, 404)


class CategoriesWordlistViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@etest.ru'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            owner=self.user
        )
        
        self.public_category = Category.objects.create(
            name='Public Category',
            description='Public description',
            owner=None
        )
        
        self.word1 = Word.objects.create(word='apple', translation='яблоко', transcription='ˈæp.əl')
        self.word1.category.add(self.category)
        
        self.word2 = Word.objects.create(word='book', translation='книга', transcription='bʊk')
        self.word2.category.add(self.category)
        self.word2.category.add(self.public_category)


    def test_unauthenticated_access(self):
        """Тест для неавторизованного пользователя"""
        response = self.client.get(reverse('categories_wordlist', args=[self.public_category.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.public_category)
        self.assertEqual(len(response.context['wordlist']), 1)
        
        word = response.context['wordlist'][0]
        self.assertEqual(word.status, 'new')
        self.assertEqual(word.repetition_count, 0)
        self.assertEqual(word.repetition_progress, 0)

    def test_authenticated_access_own_category(self):
        """Тест для авторизованного пользователя со своей категорией"""
        Word_Repetition.objects.create(
            user=self.user,
            word=self.word1,
            repetition_count=3,
            next_review=timezone.now() + timezone.timedelta(days=1)
        )
        Learned_Word.objects.create(user=self.user, word=self.word2)
        
        self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('categories_wordlist', args=[self.category.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['wordlist']), 2)
        
        words = {w.word: w for w in response.context['wordlist']}
        
        self.assertEqual(words['apple'].status, 'in_progress')
        self.assertEqual(words['apple'].repetition_count, 3)
        self.assertEqual(words['apple'].repetition_progress, 60)
        
        self.assertEqual(words['book'].status, 'learned')
        self.assertEqual(words['book'].repetition_count, 0)

    def test_authenticated_access_public_category(self):
        """Тест для авторизованного пользователя с публичной категорией"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('categories_wordlist', args=[self.public_category.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['wordlist']), 1)
        self.assertEqual(response.context['wordlist'][0].status, 'new')

    def test_access_nonexistent_category(self):
        """Тест с несуществующей категорией"""
        response = self.client.get(reverse('categories_wordlist', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_highlight_parameter(self):
        """Тест с параметром highlight"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(
            reverse('categories_wordlist', args=[self.category.id]) + '?highlight=apple'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['highlight_word'], 'apple')

    def test_access_foreign_private_category(self):
        """Тест доступа к чужой категории"""
        private_category = Category.objects.create(
            name='Private',
            description='Private desc',
            owner=self.other_user
        )
        
        self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('categories_wordlist', args=[private_category.id]))
        
        self.assertEqual(response.status_code, 403) 

    def test_word_progress_calculation(self):
        """Тест расчета прогресса изучения слов"""
        Word_Repetition.objects.create(
            user=self.user,
            word=self.word1,
            repetition_count=5,
            next_review=timezone.now() + timezone.timedelta(days=1)
        )
        
        self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('categories_wordlist', args=[self.category.id]))
        
        word = next(w for w in response.context['wordlist'] if w.word == 'apple')
        self.assertEqual(word.repetition_progress, 100)

    def test_multiple_categories_word(self):
        """Тест слова, принадлежащего нескольким категориям"""
        new_category = Category.objects.create(name='New Category', owner=self.user)
        self.word1.category.add(new_category)
        
        self.client.login(username='testuser', password='123')
        response = self.client.get(reverse('categories_wordlist', args=[new_category.id]))
        
        self.assertEqual(len(response.context['wordlist']), 1)
        self.assertEqual(response.context['wordlist'][0].word, 'apple')


class FeedbackViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('feedback')
        self.valid_data = {
            'name': 'testname',
            'email': 'testname@test.ru',
            'message': 'Test message'
        }

    def test_get_request(self):
        """Тест GET-запроса (отображение формы)"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/feedback.html')
        self.assertIsInstance(response.context['form'], FeedbackForm)
        self.assertContains(response, 'id="id_name"')
        self.assertContains(response, 'class="form-control"')

    def test_valid_post_request(self):
        """Тест успешной отправки формы"""
        response = self.client.post(self.url, data=self.valid_data, follow=True)
        
        # Проверка редиректа
        self.assertRedirects(response, self.url)
        
        # Проверка создания записи в БД
        self.assertEqual(Feedback.objects.count(), 1)
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.name, 'testname')
        self.assertEqual(feedback.email, 'testname@test.ru')
        self.assertEqual(feedback.message, 'Test message')

    def test_invalid_post_request(self):
        """Тест с невалидными данными"""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.url, data=invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(Feedback.objects.count(), 0)

    def test_empty_fields(self):
        """Тест с пустыми обязательными полями"""
        required_fields = ['name', 'email', 'message']
        
        for field in required_fields:
            with self.subTest(field=field):
                invalid_data = self.valid_data.copy()
                invalid_data[field] = ''
                
                response = self.client.post(self.url, data=invalid_data)
                
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context['form'].is_valid())
                self.assertIn(field, response.context['form'].errors)
                self.assertEqual(Feedback.objects.count(), 0)

    def test_form_field_classes(self):
        """Тест наличия CSS-классов у полей формы"""
        form = FeedbackForm()
        
        self.assertEqual(form.fields['name'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['email'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['message'].widget.attrs['class'], 'form-control')

    def test_long_input(self):
        """Тест с очень длинными значениями"""
        long_data = {
            'name': 'И' * 2000,  
            'email': 'long_email@' + 'x' * 2000 + '.ru',
            'message': 'Msg' * 1000
        }
        
        response = self.client.post(self.url, data=long_data)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context['form'].errors), 0)

    def test_created_at(self):
        """Тест времени создания"""
        before = timezone.now()
        self.client.post(self.url, data=self.valid_data)
        after = timezone.now()
        feedback = Feedback.objects.first()
        self.assertTrue(before <= feedback.created_at <= after)


class ResetCategoryProgressViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='123'
        )
    
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            owner=self.user
        )
        
        self.word1 = Word.objects.create(word='apple', translation='яблоко')
        self.word1.category.add(self.category)
        
        self.word2 = Word.objects.create(word='book', translation='книга')
        self.word2.category.add(self.category)

    def test_unauthenticated_access(self):
        """Тест доступа для неавторизованного пользователя"""
        response = self.client.get(
            reverse('reset_category_progress', args=[self.category.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_reset_progress(self):
        """Тест сброса прогресса по категории"""
        Learned_Word.objects.create(user=self.user, word=self.word1)
        Word_Repetition.objects.create(
            user=self.user,
            word=self.word2,
            repetition_count=3,
            next_review=timezone.now() + timezone.timedelta(days=1)
        )
        
        self.client.login(username='testuser', password='123')
        response = self.client.post(
            reverse('reset_category_progress', args=[self.category.id]),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('categories_wordlist', args=[self.category.id])
        )
        self.assertFalse(
            Learned_Word.objects.filter(user=self.user, word__category=self.category).exists()
        )
        self.assertFalse(
            Word_Repetition.objects.filter(user=self.user, word__category=self.category).exists()
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            f'Прогресс по категории "{self.category.name}" сброшен'
        )

    def test_reset_empty_category(self):
        """Тест сброса пустой категории"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(
            reverse('reset_category_progress', args=[self.category.id]),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)

    def test_reset_foreign_category(self):
        """Тест попытки сброса чужой категории"""
        other_category = Category.objects.create(
            name='Other Category',
            owner=self.other_user
        )
        
        self.client.login(username='testuser', password='123')
        response = self.client.post(
            reverse('reset_category_progress', args=[other_category.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_nonexistent_category(self):
        """Тест с несуществующей категорией"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(
            reverse('reset_category_progress', args=[9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_get_request(self):
        """Тест GET-запроса"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(
            reverse('reset_category_progress', args=[self.category.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('categories_wordlist', args=[self.category.id])
        )


class WordStartLearningTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='123',
            email='other@test.ru'
        )
        
        self.category_user = Category.objects.create(
            name='User Category',
            owner=self.user
        )
        self.category_common = Category.objects.create(
            name='Common Category',
            owner=None
        )
        self.category_other = Category.objects.create(
            name='Other User Category',
            owner=self.other_user
        )
        
        self.word_user = Word.objects.create(word='user_word', translation='слово пользователя')
        self.word_user.category.add(self.category_user)
        
        self.word_common = Word.objects.create(word='common_word', translation='общее слово')
        self.word_common.category.add(self.category_common)
        
        self.word_other = Word.objects.create(word='other_word', translation='чужое слово')
        self.word_other.category.add(self.category_other)
        
        self.url_user = reverse('word_start_learning', args=[self.word_user.id])
        self.url_common = reverse('word_start_learning', args=[self.word_common.id])
        self.url_other = reverse('word_start_learning', args=[self.word_other.id])


    def test_unauthenticated_access(self):
        """Неавторизованный пользователь получает 302"""
        response = self.client.post(self.url_user)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_success(self):
        """Успешное добавление слова в изучение"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_user)
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Слово добавлено в изучаемые')
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_user
            ).exists()
        )

    def test_existing_repetition(self):
        """Повторное добавление уже изучаемого слова"""
        Word_Repetition.objects.create(user=self.user, word=self.word_user)
        
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_user)
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_user
            ).count(),
            1
        )

    def test_nonexistent_word(self):
        """Попытка добавить несуществующее слово"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(reverse('word_start_learning', args=[9999]))
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Слово не найдено', data['message'])

    def test_common_word_access(self):
        """Доступ к слову из общей категории"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_common)
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_common
            ).exists()
        )
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_common
            ).exists()
        )

    def test_foreign_word_access(self):
        """Попытка доступа к слову другого пользователя"""
        
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_other)
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['status'], 'error')
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )

    def test_get_request(self):
        """GET-запрос должен возвращать ошибку"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url_user)
        self.assertEqual(response.status_code, 405)

    def test_default_repetition_values(self):
        """Проверка установки значений по умолчанию"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_user)
        
        repetition = Word_Repetition.objects.get(user=self.user, word=self.word_user)
        self.assertEqual(repetition.repetition_count, 0)
        self.assertIsNotNone(repetition.next_review)

    def test_word_in_common_and_foreign_category(self):
        """Слово есть в общей категории и в чужой"""
        shared_word = Word.objects.create(
            word='shared',
            translation='общее',
            transcription='ʃeəd'
        )
        shared_word.category.add(self.category_common)
        shared_word.category.add(self.category_other)

        self.client.login(username='testuser', password='123')
        response = self.client.post(reverse('word_start_learning', args=[shared_word.id]))

        self.assertEqual(response.status_code, 200)

    def test_word_only_in_foreign_category(self):
        """Слово есть только в чужой категории"""
        foreign_word = Word.objects.create(
            word='foreign',
            translation='чужое',
            transcription='ˈfɒr.ən'
        )
        foreign_word.category.add(self.category_other)

        self.client.login(username='testuser', password='123')
        response = self.client.post(reverse('word_start_learning', args=[foreign_word.id]),)

        self.assertEqual(response.status_code, 403)

class WordMarkKnownTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='123',
            email='other@test.ru'
        )
        
        self.category_user = Category.objects.create(
            name='User Category',
            owner=self.user
        )
        self.category_common = Category.objects.create(
            name='Common Category',
            owner=None
        )
        self.category_other = Category.objects.create(
            name='Other User Category',
            owner=self.other_user
        )
        
        self.word_user = Word.objects.create(word='user_word', translation='слово пользователя')
        self.word_user.category.add(self.category_user)
        
        self.word_common = Word.objects.create(word='common_word', translation='общее слово')
        self.word_common.category.add(self.category_common)
        
        self.word_other = Word.objects.create(word='other_word', translation='чужое слово')
        self.word_other.category.add(self.category_other)
        
        self.url_user = reverse('word_mark_known', args=[self.word_user.id])
        self.url_common = reverse('word_mark_known', args=[self.word_common.id])
        self.url_other = reverse('word_mark_known', args=[self.word_other.id])

    def test_unauthenticated_access(self):
        """Неавторизованный пользователь получает 302"""
        response = self.client.post(self.url_user)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_success_user_word(self):
        """Успешное помечение своего слова как известного"""
        self.client.login(username='testuser', password='123')
        Word_Repetition.objects.create(user=self.user, word=self.word_user)
        
        response = self.client.post(self.url_user)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Слово помечено как известное')

        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_user
            ).exists()
        )
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_user
            ).exists()
        )

    def test_authenticated_success_common_word(self):
        """Успешное помечение общего слова как известного"""
        self.client.login(username='testuser', password='123')
        Word_Repetition.objects.create(user=self.user, word=self.word_common)
        Word_Repetition.objects.create(user=self.other_user, word=self.word_common)

        response = self.client.post(self.url_common)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')

        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_common
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                user=self.other_user,
                word=self.word_common
            ).exists()
        )
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_common
            ).exists()
        )
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_common
            ).exists()
        )

    def test_mark_already_known_word(self):
        """Повторное помечение уже известного слова"""
        self.client.login(username='testuser', password='123')
        Learned_Word.objects.create(user=self.user, word=self.word_user)
        
        response = self.client.post(self.url_user)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_user
            ).count(),
            1
        )

    def test_foreign_word_access(self):
        """Попытка пометить чужое слово как известное"""
        self.client.login(username='testuser', password='123')
        Word_Repetition.objects.create(user=self.other_user, word=self.word_other)
        
        response = self.client.post(self.url_other)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Нет доступа к этому слову')
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_other
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_other
            ).exists()
        )

    def test_nonexistent_word(self):
        """Попытка пометить несуществующее слово"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(reverse('word_mark_known', args=[9999]))
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Слово не найдено', data['message'])

    def test_get_request(self):
        """GET-запрос должен возвращать ошибку"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url_user)
        self.assertEqual(response.status_code, 405)

    def test_mark_known_word_in_common_and_foreign_category(self):
        """Слово есть в общей и чужой категории - доступ разрешен"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_common)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Learned_Word.objects.filter(user=self.user, word=self.word_common).exists())

    def test_mark_known_word_only_in_foreign_category(self):
        """Слово только в чужой категории - доступ запрещен"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_other)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Learned_Word.objects.filter(user=self.user, word=self.word_other).exists())

class WordResetProgressTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='123',
            email='other@test.ru'
        )
        
        self.category_user = Category.objects.create(
            name='User Category',
            owner=self.user
        )
        self.category_common = Category.objects.create(
            name='Common Category',
            owner=None
        )
        self.category_other = Category.objects.create(
            name='Other User Category',
            owner=self.other_user
        )
        
        self.word_user = Word.objects.create(word='user_word', translation='слово пользователя')
        self.word_user.category.add(self.category_user)
        
        self.word_common = Word.objects.create(word='common_word', translation='общее слово')
        self.word_common.category.add(self.category_common)
        
        self.word_other = Word.objects.create(word='other_word', translation='чужое слово')
        self.word_other.category.add(self.category_other)
        
        self.url_user = reverse('word_reset_progress', args=[self.word_user.id])
        self.url_common = reverse('word_reset_progress', args=[self.word_common.id])
        self.url_other = reverse('word_reset_progress', args=[self.word_other.id])

    def test_unauthenticated_access(self):
        """Неавторизованный пользователь получает 302"""
        response = self.client.post(self.url_user)
        self.assertEqual(response.status_code, 302)

    def test_reset_progress_user_word(self):
        """Успешный сброс прогресса для своего слова"""
        self.client.login(username='testuser', password='123')
        
        Word_Repetition.objects.create(
            user=self.user,
            word=self.word_user,
            next_review=timezone.now(),
            repetition_count=5
        )
        Learned_Word.objects.create(user=self.user, word=self.word_user)
        
        response = self.client.post(self.url_user)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Прогресс по слову сброшен')
        
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_user
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_user
            ).exists()
        )

    def test_reset_progress_common_word(self):
        """Успешный сброс прогресса для общего слова"""
        self.client.login(username='testuser', password='123')

        Word_Repetition.objects.create(
            user=self.user,
            word=self.word_common,
            next_review=timezone.now(),
            repetition_count=5
        )
        Learned_Word.objects.create(user=self.user, word=self.word_common)  
        Word_Repetition.objects.create(
            user=self.other_user,
            word=self.word_common,
            next_review=timezone.now(),
            repetition_count=4
        )
        Learned_Word.objects.create(user=self.other_user, word=self.word_common)  

        response = self.client.post(self.url_common)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_common
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_common
            ).exists()
        )
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_common
            ).exists()
        )
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.other_user,
                word=self.word_common
            ).exists()
        )

    def test_reset_progress_without_existing_records(self):
        """Сброс прогресса когда нет записей о прогрессе"""
        self.client.login(username='testuser', password='123')
        
        response = self.client.post(self.url_user)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')

    def test_foreign_word_access(self):
        """Попытка сбросить прогресс чужого слова"""
        self.client.login(username='testuser', password='123')
        Word_Repetition.objects.create(
            user=self.other_user,
            word=self.word_other,
            next_review=timezone.now(),
            repetition_count=4
        )
        Learned_Word.objects.create(user=self.other_user, word=self.word_other)
        
        response = self.client.post(self.url_other)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Нет доступа к этому слову')
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )

    def test_nonexistent_word(self):
        """Попытка сбросить прогресс несуществующего слова"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(reverse('word_reset_progress', args=[9999]))
        
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Слово не найдено', data['message'])

    def test_get_request(self):
        """GET-запрос должен возвращать ошибку"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url_user)
        self.assertEqual(response.status_code, 405)


    def test_reset_word_in_common_and_foreign_category(self):
        """Сброс прогресса для слова в общей и чужой категории - доступ разрешен"""
        self.client.login(username='testuser', password='123')
        Word_Repetition.objects.create(user=self.user, word=self.word_common)
        Learned_Word.objects.create(user=self.user, word=self.word_common)
        
        response = self.client.post(self.url_common)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Word_Repetition.objects.filter(user=self.user, word=self.word_common).exists())
        self.assertFalse(Learned_Word.objects.filter(user=self.user, word=self.word_common).exists())

    def test_reset_word_only_in_foreign_category(self):
        """Сброс прогресса для слова только в чужой категории - доступ запрещен"""
        self.client.login(username='testuser', password='123')
        response = self.client.post(self.url_other)
        self.assertEqual(response.status_code, 403)


class AddWordToCategoryViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='123',
            email='test@test.ru'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='123',
            email='other@other.ru'
        )
        
        self.category_user = Category.objects.create(
            name='User Category',
            owner=self.user
        )
        self.category_common = Category.objects.create(
            name='Common Category',
            owner=None
        )
        self.category_other = Category.objects.create(
            name='Other Category',
            owner=self.other_user
        )
        
        self.existing_word_user = Word.objects.create(
            word='apple',
            translation='яблоко',
            transcription='ˈæp.əl'
        )
        self.existing_word_user.category.add(self.category_user)
        
        self.word_common = Word.objects.create(
            word='book',
            translation='книга',
            transcription='bʊk'
        )
        self.word_common.category.add(self.category_common)
        
        self.word_other = Word.objects.create(
            word='table',
            translation='стол',
            transcription='ˈteɪbəl'
        )
        self.word_other.category.add(self.category_other)
        
        self.url = reverse('add_word_to_category', args=[self.category_user.id])
        self.url_common = reverse('add_word_to_category', args=[self.category_common.id])
        self.url_other = reverse('add_word_to_category', args=[self.category_other.id])

    def test_unauthenticated_access(self):
        """Неавторизованный пользователь получает 302"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_foreign_category_access_denied(self):
        """Попытка доступа к чужой категории возвращает 404"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url_other)
        self.assertEqual(response.status_code, 404)

    def test_get_request_renders_form(self):
        """GET-запрос возвращает форму для авторизованного пользователя"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'web/add_word.html')
        self.assertIsInstance(response.context['form'], AddWordForm)
        self.assertEqual(response.context['category'], self.category_user)

    def test_add_new_word_success(self):
        """Успешное добавление полностью нового слова"""
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'dog',
            'translation': 'собака',
            'transcription': 'dɒɡ'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        
        word = Word.objects.get(word='dog')
        self.assertEqual(word.translation, 'собака')
        self.assertEqual(word.transcription, 'dɒɡ')
        self.assertTrue(word.category.filter(id=self.category_user.id).exists())
        
        self.assertFalse(
            Word_Repetition.objects.filter(
                word=word
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                word=word
            ).exists()
        )
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(str(messages_list[0]), 'Слово успешно создано и добавлено')

    def test_add_word_with_minimal_data(self):
        """Добавление слова с минимальными данными (без транскрипции)"""
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'dog',
            'translation': 'собака',
            'transcription': ''
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        
        word = Word.objects.get(word='dog')
        self.assertEqual(word.translation, 'собака')
        self.assertEqual(word.transcription, '')
        self.assertTrue(word.category.filter(id=self.category_user.id).exists())
        
        self.assertFalse(
            Word_Repetition.objects.filter(
                word=word
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                word=word
            ).exists()
        )
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(str(messages_list[0]), 'Слово успешно создано и добавлено')

    def test_form_validation_empty_fields(self):
        """Проверка валидации пустых полей"""
        self.client.login(username='testuser', password='123')
        data = {
            'word': '',
            'translation': '',
            'transcription': ''
        }
        
        response = self.client.post(self.url, data)
        form = response.context.get('form')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(form.errors['word'], ['Поле "Английское слово" обязательно для заполнения'])
        self.assertEqual(form.errors['translation'], ['Поле "Перевод" обязательно для заполнения'])
    
    def test_form_validation_max_length(self):
        """Проверка максимальной длины полей"""
        self.client.login(username='testuser', password='123')
        long_str = 'a' * 51
        data = {
            'word': long_str,
            'translation': long_str,
            'transcription': long_str
        }
        
        response = self.client.post(self.url, data)
        form = response.context.get('form')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(form.errors['word'], ['Максимальная длина английского слова - 50 символов'])
        self.assertEqual(form.errors['translation'], ['Максимальная длина перевода - 50 символов'])
        self.assertEqual(form.errors['transcription'], ['Максимальная длина транскрипции - 50 символов'])
     
    def test_form_validation_whitespace(self):
        """Проверка обработки пробельных символов"""
        self.client.login(username='testuser', password='123')
        data = {
           'word': '  dog ',
            'translation': '    собака'   ,
            'transcription': '  dɒɡ '
        }
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, 302)
        word = Word.objects.get(word='dog')
        self.assertEqual(word.translation, 'собака')
        self.assertEqual(word.transcription, 'dɒɡ')

    def test_add_existing_word_to_same_category(self):
        """Попытка добавить существующее слово в ту же категорию"""
        Word.objects.create(
            word='existing',
            translation='существующий',
            transcription='ɪɡˈzɪstɪŋ'
        ).category.add(self.category_user)
        
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'Existing',
            'translation': 'существующий',
            'transcription': 'ɪɡˈzɪstɪŋ'
        }
        
        response = self.client.post(self.url, data)
        form = response.context.get('form')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(form.errors['word'], ['Это слово уже есть в данной категории'])
        self.assertEqual(Word.objects.filter(word__iexact='existing').count(), 1)

    def test_add_existing_word_to_different_category(self):
        """Добавление существующего слова в другую категорию"""
        word = Word.objects.create(
            word='shared',
            translation='общий',
            transcription='ʃeərd'
        )
        word.category.add(self.category_common)
        
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'shared',
            'translation': 'общий',
            'transcription': 'ʃeərd'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertTrue(word.category.filter(id=self.category_user.id).exists())
        self.assertEqual(Word.objects.filter(word='shared').count(), 1)

    def test_same_word_different_translation(self):
        """Совпадает слово, но отличается перевод -> новое слово"""
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'apple',
            'translation': 'яблочный',
            'transcription': 'ˈæp.əl'
        }
        
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(Word.objects.filter(word__iexact='apple').count(), 2)
        self.assertTrue(Word.objects.filter(word='apple', translation='яблочный').exists())

    def test_same_word_different_transcription(self):
        """Совпадает слово, но отличается транскрипция -> новое слово"""
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'apple',
            'translation': 'яблоко',
            'transcription': 'æpl'
        }
        
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(Word.objects.filter(word__iexact='apple').count(), 2)
        self.assertTrue(Word.objects.filter(word='apple', transcription='æpl').exists())

    def test_add_new_from_user_other_category(self):
        """Добавление слова из другой категории пользователя, которое незнакомое"""
        other_user_category = Category.objects.create(
            name='Another User Category',
            owner=self.user
        )
        word = Word.objects.create(
            word='pen',
            translation='ручка',
            transcription='pen'
        )
        word.category.add(other_user_category)
        
        self.client.login(username='testuser', password='123')
        data = {
            'word': 'pen',
            'translation': 'ручка',
            'transcription': 'pen'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(word.category.count(), 2)
        self.assertTrue(word.category.filter(id=self.category_user.id).exists())
        
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=word
            ).exists()
        )

    def test_add_repeat_from_user_other_category(self):
        """Добавление слова из другой категории пользователя, которое на повторе"""
        other_user_category = Category.objects.create(
            name='Another User Category',
            owner=self.user
        )
        word = Word.objects.create(
            word='pen',
            translation='ручка',
            transcription='pen'
        )
        word.category.add(other_user_category)
        Word_Repetition.objects.create(user=self.user, word=word)

        self.client.login(username='testuser', password='123')
        data = {
            'word': 'pen',
            'translation': 'ручка',
            'transcription': 'pen'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(word.category.count(), 2)
        self.assertTrue(word.category.filter(id=self.category_user.id).exists())
        
        self.assertEqual(
            Word_Repetition.objects.filter(
                user=self.user,
                word=word
            ).count(),
            1
        )
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.user,
                word=word
            ).exists()
        )

    def test_add_learned_from_user_other_category(self):
        """Добавление слова из другой категории пользователя, которое изучено"""
        other_user_category = Category.objects.create(
            name='Another User Category',
            owner=self.user
        )
        word = Word.objects.create(
            word='pen',
            translation='ручка',
            transcription='pen'
        )
        word.category.add(other_user_category)
        Learned_Word.objects.create(user=self.user, word=word)

        self.client.login(username='testuser', password='123')
        data = {
            'word': 'pen',
            'translation': 'ручка',
            'transcription': 'pen'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(word.category.count(), 2)
        self.assertTrue(word.category.filter(id=self.category_user.id).exists())
        
        self.assertEqual(
            Learned_Word.objects.filter(
                user=self.user,
                word=word
            ).count(),
            1
        )
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.user,
                word=word
            ).exists()
        )

    def test_add_from_common_category(self):
        """Добавление слова из общей категории"""
        self.client.login(username='testuser', password='123')
        Learned_Word.objects.create(user=self.user, word=self.word_common)
        data = {
            'word': self.word_common.word,
            'translation': self.word_common.translation,
            'transcription': self.word_common.transcription
        }
        
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(self.word_common.category.count(), 2)
        self.assertTrue(self.word_common.category.filter(id=self.category_user.id).exists())
        
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_common
            ).exists()
        )

    def test_add_from_foreign_category(self):
        """Добавление слова из чужой категории создает новый прогресс"""
        self.client.login(username='testuser', password='123')
        Learned_Word.objects.create(
            user=self.other_user,
            word=self.word_other
        )
        Word_Repetition.objects.create(
            user=self.other_user,
            word=self.word_other
        )
        data = {
            'word': self.word_other.word,
            'translation': self.word_other.translation,
            'transcription': self.word_other.transcription
        }
        
        self.assertEqual(self.word_other.category.count(), 1)
        response = self.client.post(self.url, data)
        
        self.assertRedirects(response, reverse('categories_wordlist', args=[self.category_user.id]))
        self.assertEqual(self.word_other.category.count(), 2)
        self.assertTrue(self.word_other.category.filter(id=self.category_user.id).exists())
        
        self.assertEqual(Word.objects.filter(id=self.word_other.id).count(), 1)
        self.assertEqual(Word.objects.filter(
            word=self.word_other.word,
            translation=self.word_other.translation,
            transcription=self.word_other.transcription
        ).count(), 1)
        self.assertTrue(
            Learned_Word.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )
        self.assertTrue(
            Word_Repetition.objects.filter(
                user=self.other_user,
                word=self.word_other
            ).exists()
        )
        self.assertFalse(
            Learned_Word.objects.filter(
                user=self.user,
                word=self.word_other
            ).exists()
        )
        self.assertFalse(
            Word_Repetition.objects.filter(
                user=self.user,
                word=self.word_other
            ).exists()
        )
