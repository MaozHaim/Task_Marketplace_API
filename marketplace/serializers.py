from rest_framework import serializers
from .models import Job, Application


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        # The owner is the user that posted the job
        # The user can't mark that he is hired and can't change the creation time of the job
        read_only_fields = ['owner', 'created_at', 'status']


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
        # The user can't mark that he is hired and can't change the submission time of his application
        read_only_fields = ['is_hired', 'submitted_at']
