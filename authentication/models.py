# imports
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# Create your models here.

# user manager


class UserManager(BaseUserManager):
    # create user
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Enter a valid email')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    # create staff user
    def create_staffuser(self, email, password=None, **extra_fields):
        extra_fields['staff'] = True
        return self.create_user(email, password, **extra_fields)

    # create super user / admin
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields['staff'] = True
        extra_fields['admin'] = True
        return self.create_user(email, password, **extra_fields)

# user model


class User(AbstractBaseUser):
    genders = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others'),
    )
    email = models.EmailField(max_length=245, unique=True)
    first_name = models.CharField(max_length=245)
    last_name = models.CharField(max_length=245)
    gender = models.CharField(max_length=245, choices=genders)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    # username replaced with email
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    # There is no per-object permission system on this model, so only
    # admins hold permissions. Staff users can log in to the admin site
    # but cannot view or change anything unless they are also admins.
    def has_perm(self, perm, obj=None):
        return self.is_active and self.admin

    def has_module_perms(self, app_label):
        return self.is_active and self.admin

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_superuser(self):
        return self.admin
