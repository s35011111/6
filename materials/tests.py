from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from materials.models import Lesson, Course

User = get_user_model()


class LessonViewSetTests(APITestCase):

    def setUp(self):
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            password='password123',
            phone='+1234567890'
        )

        self.another_user = User.objects.create_user(
            email='another@example.com',
            password='password123',
            phone='+1234567891'
        )

        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            phone='+1234567892',
            is_staff=True
        )

        self.Course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            author = self.another_user
        )

        self.lesson1 = Lesson.objects.create(
            name='First lesson',
            description='description of first lesson',
            author=self.regular_user,
            course=self.Course
        )

        self.lesson2 = Lesson.objects.create(
            name='Second lesson',
            description='description of second lesson',
            author=self.another_user,
            course=self.Course
        )

        self.list_url = reverse('lesson-list')
        self.detail_url = reverse('lesson-detail', kwargs={'pk': self.lesson1.id})

        self.client.force_authenticate(user=None)

    def tearDown(self):
        pass
    def test_list_lessons_unauthenticated(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_lessons_authenticated(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_lessons_with_filter(self):
        url = f"{self.list_url}?course={self.Course.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_lessons_search(self):
        url = f"{self.list_url}?search=First"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_lesson_unauthenticated(self):
        data = {
            'name': 'New lesson',
            'description': 'This is a new lesson',
            'course': self.Course.id
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_lesson_authenticated(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'name': 'My New lesson',
            'description': 'This is my new lesson description without links.',
            'course': self.Course.id
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My New lesson')
        self.assertEqual(response.data['course'], self.Course.id)

        self.assertTrue(
            Lesson.objects.filter(name='My New lesson').exists()
        )

    def test_create_lesson_with_links_should_fail(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'name': 'lesson with link',
            'description': 'Check out https://example.com',
            'course': self.Course.id
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)

    def test_create_lesson_invalid_Course(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'name': 'Invalid lesson',
            'description': 'description',
            'course': 999
        }

        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_lesson_unauthenticated(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        #self.assertEqual(response.data['id'], self.lesson1.id)
        #self.assertEqual(response.data['name'], 'First lesson')

    def test_retrieve_nonexistent_post(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('lesson-detail', kwargs={'pk': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_post(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'name': 'Updated name',
            'description': 'Updated description without links',
            'course': self.Course.id
        }

        response = self.client.put(self.detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated name')

        self.lesson1.refresh_from_db()
        self.assertEqual(self.lesson1.name, 'Updated name')

    def test_partial_update_own_post(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'name': 'Partially Updated'
        }

        response = self.client.patch(self.detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Partially Updated')

    def test_update_other_users_lesson_should_fail(self):
        self.client.force_authenticate(user=self.another_user)

        data = {'name': 'Unauthorized Update'}
        response = self.client.patch(self.detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_update_any_post(self):
        self.client.force_authenticate(user=self.admin_user)

        data = {'name': 'Updated by Admin'}
        response = self.client.patch(self.detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_with_links_should_fail(self):
        self.client.force_authenticate(user=self.regular_user)

        data = {
            'description': 'Updated with link https://example.com'
        }

        response = self.client.patch(self.detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_delete_own_post(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Lesson.DoesNotExist):
            Lesson.objects.get(id=self.lesson1.id)

    def test_delete_other_users_lesson_should_fail(self):
        self.client.force_authenticate(user=self.another_user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_delete_any_post(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_nonexistent_post(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse('lesson-detail', kwargs={'pk': 999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)






    def test_permissions_based_on_user_role(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.list_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.regular_user)

        data = {
            'name': 'User lesson',
            'description': 'description',
            'course': self.Course.id
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.patch(self.detail_url, {'name': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        other_lesson_url = reverse('lesson-detail', kwargs={'pk': self.lesson2.id})
        response = self.client.patch(other_lesson_url, {'name': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(self.detail_url, {'name': 'Admin Updated'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

