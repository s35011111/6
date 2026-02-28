from django.test import TestCase

# Create your tests here.
from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import Subscription
from materials.models import Lesson, Course

User = get_user_model()


class SubscriptionViewSetTests(APITestCase):

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

        self.course1 = Course.objects.create(
            name='Test Course',
            description='Test Description',
            author = self.another_user
        )
        self.course2 = Course.objects.create(
            name='Test course two',
            description='Description of course two',
            author=self.another_user
        )


        self.subscription1 = Subscription.objects.create(
            course=self.course1,
            user = self.regular_user
        )
        self.subscription2 = Subscription.objects.create(
            course=self.course2,
            user = self.another_user
        )

        self.list_url = reverse('lesson-list')


        self.client.force_authenticate(user=None)

        self.client = APIClient()

    def tearDown(self):
        pass

    def authenticate_user(self, user):

        self.client.force_authenticate(user=user)

    def test_unauthenticated_access(self):

        url = reverse('subscription-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_view_own_subscriptions(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 4)

        self.assertEqual(response.data['results'][0]['user'], self.regular_user.id)

    def test_create_subscription(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-list')

        data = {
            'user': self.regular_user.id,
            'course': self.course1.id
        }

        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code,[status.HTTP_405_METHOD_NOT_ALLOWED,status.HTTP_400_BAD_REQUEST])
        self.assertEqual(Subscription.objects.count(), 2)

    def test_create_duplicate_subscription(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-list')

        data = {
            'user': self.regular_user.id,
            'course': self.course2.id
        }

        response = self.client.post(url, data, format='json')

        self.assertIn(response.status_code,
                      [status.HTTP_400_BAD_REQUEST,status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_201_CREATED])

    """     def test_retrieve_subscription(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-detail', args=[self.subscription1.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.subscription1.id)

    def test_update_subscription(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-detail', args=[self.subscription1.id])


        data = {
            'user': self.regular_user.id,
            'course': self.course2.id,

        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    def test_delete_subscription(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-detail', args=[self.subscription1.id])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Subscription.objects.count(), 1)

    def test_user_cannot_access_others_subscriptions(self):

        self.authenticate_user(self.regular_user)


        url = reverse('subscription-detail', args=[self.subscription2.id])
        response = self.client.get(url)


        self.assertIn(response.status_code,
                      [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
"""
    def test_admin_can_access_all_subscriptions(self):

        admin_user = User.objects.create_superuser(
            email='adminadmin@example.com',
            password='password123',
            is_staff=True
        )
        self.authenticate_user(admin_user)

        url = reverse('subscription-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_create_subscription_nonexistent_course(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-list')

        data = {
            'user': self.regular_user.id,
            'course': 99999
        }

        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code,
                         [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_400_BAD_REQUEST])

    def test_create_subscription_different_user(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-list')

        data = {
            'user': self.another_user.id,
            'course': self.course1.id
        }

        response = self.client.post(url, data, format='json')

        self.assertIn(response.status_code,
                      [status.HTTP_405_METHOD_NOT_ALLOWED,status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])

    def test_subscription_to_own_course(self):

        self.authenticate_user(self.regular_user)
        url = reverse('subscription-list')

        data = {
            'user': self.regular_user.id,
            'course': self.course1.id
        }

        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code,
                      [status.HTTP_405_METHOD_NOT_ALLOWED,status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST])


