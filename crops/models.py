import os
import requests
from io import BytesIO
from urllib.parse import urlparse
from django.core.files import File
from django.db import models
from django.utils.text import slugify
from uuid import uuid4
from django.core.files.base import ContentFile
from django.utils.text import slugify

def crop_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.name}_{uuid4().hex[:8]}.{ext}"
    return os.path.join('crops', filename)

class Crop(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to=crop_image_path, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text="Paste image URL here if not uploading manually.")
    description = models.TextField(blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)
    health_contents = models.TextField(blank=True, null=True)
    conditions_of_growth = models.TextField(blank=True, null=True)
    link_to_wikipedia = models.URLField(blank=True, null=True, help_text="Link to Wikipedia page for this crop.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crops'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image_url and not self.image:
            try:
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    url_path = urlparse(self.image_url).path
                    ext = os.path.splitext(url_path)[-1] or '.jpg'
                    file_name = f"{slugify(self.name)}{ext}"
                    image_file = BytesIO(response.content)
                    self.image.save(file_name, File(image_file), save=False)
            except Exception as e:
                print(f"❌ Failed to fetch image from URL: {e}")
        super().save(*args, **kwargs)


# nutrients model
class Nutrients(models.Model):
    name = models.CharField(max_length=255, unique=True)
    intro = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    links = models.TextField(blank=True, help_text="Comma-separated or JSON list of links")

    image_url = models.URLField(blank=True, help_text="URL of the image to download")
    photo = models.ImageField(upload_to='nutrients/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # If image_url is given but no local photo yet, download it
        if self.image_url and not self.photo:
            try:
                response = requests.get(self.image_url, timeout=10)
                if response.status_code == 200:
                    filename = f"{slugify(self.name)}.jpg"
                    self.photo.save(filename, ContentFile(response.content), save=False)
            except Exception as e:
                print(f"Image download failed: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name