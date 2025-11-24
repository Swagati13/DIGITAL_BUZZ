from rest_framework import serializers
from enquiries.models import Enquiry
from rest_framework import serializers
from .models import FeatureImportance, AIGeneratedReport

class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'


class FeatureImportanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureImportance
        fields = '__all__'

class AIGeneratedReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIGeneratedReport
        fields = '__all__'
