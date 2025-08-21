from django.contrib import admin
from .models import Crop  # adjust if it's a different model
from .models import Nutrients


admin.site.register(Crop)


# @admin.register(Crop)
# class CropAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name', 'description', 'image')  # or thumbnail preview

@admin.register(Nutrients)
class NutrientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'intro', 'image_url')
    search_fields = ('name', 'intro', 'description')