from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.mail import send_mail

@receiver(post_save,sender=User)
def mail_user(sender,**kwargs):
    send_mail(
    'Thank you mail',
    'Thank you for creating your account.',
    'ujjwalcomputerpro1@gmail.com',
    [send_mail],
    fail_silently=False,
)
