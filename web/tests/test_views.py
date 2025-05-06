from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser
from api.models import Category, Word, Learned_Word, Word_Repetition, Learning_Category, Feedback
from web.forms import RegistrationForm, AuthForm, FeedbackForm
import os

from django.contrib.messages import get_messages
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
        
        # Создаем тестовые данные
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
        """Тест GET-запроса (должен быть запрещен)"""
        self.client.login(username='testuser', password='123')
        response = self.client.get(
            reverse('reset_category_progress', args=[self.category.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('categories_wordlist', args=[self.category.id])
        )