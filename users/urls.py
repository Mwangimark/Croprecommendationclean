from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .views import verify_email,MyTokenObtainPairView, ContactUs


router = DefaultRouter()
router.register(r'users',UserViewSet)

urlpatterns = [
    path('',include(router.urls)),
    path('verify-email/<uidb64>/<token>/',verify_email, name='verify-email'),
    path('token/',MyTokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('contact-us/', ContactUs.as_view(), name='contact_us'),
    # path('profiles/', UserProfileView.as_view(), name='user-profile'),

]