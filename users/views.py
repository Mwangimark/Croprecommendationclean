# users/views.py
from django.conf import settings
from rest_framework.decorators import action
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password,make_password
from .utils import email_verification_token
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from .serializers import ChangePasswordSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
from .permission import IsAdmin
from django.contrib.auth import get_user_model
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from rest_framework.views import APIView
import json
import os
import random, string
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetOTP, User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Override create to send verification email after user signup
        """
        response = super().create(request, *args, **kwargs)

        # Get the newly created user from DB
        user = User.objects.get(id=response.data["id"])

        from django.conf import settings

        # Ensure they start unverified
        user.is_verified = False
        user.is_active=False
        user.save()

        

        # Import and send the email
        from .utils import send_verification_email
        send_verification_email(user, request)

        return response

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: override destroy method to set is_deleted=True
        """
        user = self.get_object()
        user.is_deleted = True
        user.save()
        return Response({'message':'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='change-password')
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            if not user.check_password(old_password):
                return Response({'old_password': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({'status': 'Password updated successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # confirming_authentication
    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        elif self.action == 'list':
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ['retrieve','update','partial_update','destroy','change_password']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
 


@api_view(['GET'])
def verify_email(request,uidb64,token):
    try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
            return HttpResponse('Invalid link',status=400)
        
    if email_verification_token.check_token(user,token):
            user.is_verified = True
            user.is_active = True
            user.save()
            return HttpResponse('Email successfully verified!',status= 200)
        
    else:
            return HttpResponse('Invalid or expired token',status = 400)
    
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class ContactUs(APIView):
    permission_classes = [AllowAny] 
    
    def post(self, request):
        message = request.data.get('message')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        address = request.data.get('address')
        city = request.data.get('city')

        full_name = f"{first_name} {last_name}"

        try:
            creds_json = os.getenv("GOOGLE_CREDENTIALS")
            if not creds_json:
                return Response({'error': 'Google credentials not found in environment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            creds_dict = json.loads(creds_json)
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")  # Fix key formatting

            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)

            sheet = client.open("contactusdata").sheet1
            sheet.append_row([full_name, email, phone, address, city, message])

            return Response({'message': 'Thank you for contacting us!'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# users dealing with forgot make_password
# system sends an otp to the email
# views.py

class SendOtp(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        # generate OTP
        otp = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        # store in DB
        PasswordResetOTP.objects.create(user=user, otp=otp, expires_at=expires_at)

        # prepare email
        html_content = render_to_string('emails/otpreceive.html', {'otp': otp, "user": user})
        email_message = EmailMultiAlternatives(
            subject="Your Password Reset OTP",
            body=f"Use this OTP to reset your password: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.attach_alternative(html_content, "text/html")

        # send in background thread
        threading.Thread(target=lambda: email_message.send(fail_silently=True)).start()

        return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)



# verify otp
# views.py
class VerifyOtp(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp).last()

            if not otp_obj:
                return Response({"error": "Invalid OTP"}, status=400)

            if otp_obj.expires_at < timezone.now():
                return Response({"error": "OTP expired"}, status=400)

            # ✅ Instead of deleting, mark as verified
            otp_obj.is_verified = True
            otp_obj.save()

            return Response({"message": "OTP verified successfully, proceed to set new password"})

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

# views.py

class ResetPassword(APIView):
    
    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(user=user, is_verified=True).last()

            if not otp_obj:
                return Response({"error": "OTP not verified"}, status=400)

            # ✅ Update password properly
            user.set_password(new_password)
            user.save()

            # Invalidate OTP
            otp_obj.delete()
            context = {
                    "user": user,
                    "login_url": settings.FRONTEND_LOGIN_URL,  # replace with your actual frontend login URL
                    "current_year": timezone.now().year,
                }

            html_content = render_to_string('emails/passwordchanged.html',context)

            # send email
            email_message = EmailMultiAlternatives(
                subject="Your Password Reset OTP",
                body=f"Your password has been successfully changed",  # fallback plain text
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send(fail_silently=False)

            return Response({"message": "Password reset successfully. You can now login."}, status=200)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
