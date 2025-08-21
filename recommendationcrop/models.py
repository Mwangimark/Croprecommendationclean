from django.db import models
from recommendation.models import Recommendation
from crops.models import Crop

class RecommendationCrop(models.Model):
    id = models.AutoField(primary_key=True)
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE,
                                       related_name='recommended_crops')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    confidence = models.FloatField()
    is_deleted = models.BooleanField(default=False) 

    class Meta:
        db_table = 'recommendation_crops'

    def __str__(self):
        return f"Crop {self.crop.name} for Recommendation {self.recommendation.id}"
