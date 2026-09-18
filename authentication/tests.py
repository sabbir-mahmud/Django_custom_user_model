from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm, UserAdminCreationForm

User = get_user_model()

STRONG_PASSWORD = 'c0rrect-horse-battery'


class UserManagerTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user('Someone@EXAMPLE.com', 'pw')
        self.assertEqual(user.email, 'Someone@example.com')
        self.assertTrue(user.check_password('pw'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user('', 'pw')

    def test_create_user_extra_fields(self):
        user = User.objects.create_user(
            'a@example.com', 'pw', first_name='Ada', gender='Female')
        self.assertEqual(user.first_name, 'Ada')
        self.assertEqual(user.gender, 'Female')

    def test_create_staffuser(self):
        user = User.objects.create_staffuser('staff@example.com', 'pw')
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user = User.objects.create_superuser('admin@example.com', 'pw')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_createsuperuser_command(self):
        call_command(
            'createsuperuser', interactive=False,
            email='cli@example.com', verbosity=0)
        self.assertTrue(User.objects.get(email='cli@example.com').is_superuser)


class PermissionTests(TestCase):
    def test_only_active_admins_have_perms(self):
        user = User.objects.create_user('u@example.com', 'pw')
        staff = User.objects.create_staffuser('s@example.com', 'pw')
        admin = User.objects.create_superuser('a@example.com', 'pw')
        for u in (user, staff):
            self.assertFalse(u.has_perm('authentication.change_user'))
            self.assertFalse(u.has_module_perms('authentication'))
        self.assertTrue(admin.has_perm('authentication.change_user'))
        self.assertTrue(admin.has_module_perms('authentication'))

        admin.is_active = False
        self.assertFalse(admin.has_perm('authentication.change_user'))


class FormTests(TestCase):
    def register_data(self, **overrides):
        data = {
            'email': 'new@example.com', 'first_name': 'New',
            'last_name': 'User', 'gender': 'Others',
            'password': STRONG_PASSWORD, 'password2': STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_form_creates_user(self):
        form = RegisterForm(data=self.register_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_register_form_password_mismatch(self):
        form = RegisterForm(data=self.register_data(password2='different1!'))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_register_form_rejects_weak_password(self):
        form = RegisterForm(
            data=self.register_data(password='123', password2='123'))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_register_form_rejects_password_similar_to_email(self):
        pw = 'new@example.com'
        form = RegisterForm(data=self.register_data(password=pw, password2=pw))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_admin_creation_form(self):
        form = UserAdminCreationForm(data={
            'email': 'x@example.com',
            'password': STRONG_PASSWORD, 'password2': STRONG_PASSWORD,
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save().check_password(STRONG_PASSWORD))


class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin@example.com', 'pw')
        self.client.force_login(self.admin)

    def test_changelist_and_add_pages_render(self):
        changelist = reverse('admin:authentication_user_changelist')
        self.assertContains(self.client.get(changelist), 'admin@example.com')
        add = reverse('admin:authentication_user_add')
        self.assertEqual(self.client.get(add).status_code, 200)

    def test_change_page_renders(self):
        url = reverse('admin:authentication_user_change', args=[self.admin.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_add_user_via_admin(self):
        response = self.client.post(reverse('admin:authentication_user_add'), {
            'email': 'added@example.com', 'first_name': 'A', 'last_name': 'B',
            'gender': 'Male', 'password': STRONG_PASSWORD,
            'password2': STRONG_PASSWORD,
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='added@example.com')
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_staff_without_admin_cannot_view_users(self):
        User.objects.create_staffuser('staff@example.com', 'pw')
        self.client.logout()
        self.assertTrue(
            self.client.login(email='staff@example.com', password='pw'))
        url = reverse('admin:authentication_user_changelist')
        self.assertEqual(self.client.get(url).status_code, 403)
