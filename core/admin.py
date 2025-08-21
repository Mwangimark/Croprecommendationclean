from django.contrib import admin
from .models import User, Crop, Recommendation, RecommendationCrop, Message



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'role', 'is_deleted')
    search_fields = ('name', 'email')
    list_filter = ('role', 'is_deleted')

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ph', 'rainfall', 'is_deleted')
    search_fields = ('user__name',)
    list_filter = ('is_deleted',)

@admin.register(RecommendationCrop)
class RecommendationCropAdmin(admin.ModelAdmin):
    list_display = ('id', 'recommendation', 'crop', 'ranking')
    search_fields = ('recommendation__id', 'crop__name')
    list_filter = ('ranking',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'is_read', 'sent_at', 'is_deleted')
    search_fields = ('sender__name', 'receiver__name', 'message')
    list_filter = ('is_read', 'is_deleted')
