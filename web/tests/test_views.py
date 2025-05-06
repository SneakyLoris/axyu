from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser
from api.models import Category, Word, Learned_Word, Word_Repetition, Learning_Category, Feedback
from web.forms import RegistrationForm
import os

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
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

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