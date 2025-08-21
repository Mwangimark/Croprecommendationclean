from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.utils.encoding import force_bytes

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user,timestamp):
        return f"{user.pk} {timestamp}{user.is_verified}"
    
    
def send_verification_email(user,request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)

    verification_url = request.build_absolute_uri(
            reverse('verify-email',kwargs={'uidb64': uid,'token':token})
        )

    subject = "Verify your email",
    message = f"Hi {user.name},\nClick the Link to verify your email: \n{verification_url}"

    send_mail(subject,message,settings.DEFAULT_FROM_EMAIL,[user.email])
    

        
email_verification_token = EmailVerificationTokenGenerator()