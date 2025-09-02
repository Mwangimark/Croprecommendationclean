from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from httplib2 import Response


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user,timestamp):
        return f"{user.pk} {timestamp}{user.is_verified}"
    
    
def send_verification_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)

    verification_link = request.build_absolute_uri(
        reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
    )

    subject = "Verify your email - Crop Recommendation System"

    # Render HTML template
    html_content = render_to_string("emails/verification_email.html", {
        "user": user,
        "verification_link": verification_link,
    })

    email = EmailMultiAlternatives(
        subject=subject,
        from_email=settings.EMAIL_HOST_USER,
        to=[user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

        
email_verification_token = EmailVerificationTokenGenerator()

