from rest_framework import serializers
from .models import Job, Application


class ApplicationSerializer(serializers.ModelSerializer):
    freelancer_name = serializers.ReadOnlyField(source='freelancer.username')
    freelancer_id = serializers.ReadOnlyField(source='freelancer.id')

    class Meta:
        model = Application
        fields = ['id', 'job', 'freelancer_name', 'freelancer_id', 'bid_price', 'is_hired', 'submitted_at']
        # The user can't mark that he is hired, can't change the submission time of his application,
        # and can't change his name or id
        read_only_fields = ['is_hired', 'submitted_at', 'freelancer_name', 'freelancer_id']


class JobSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.username')
    owner_id = serializers.ReadOnlyField(source='owner.id')

    class Meta:
        model = Job
        fields = ['id', 'owner_name', 'owner_id', 'title', 'description', 'created_at', 'status', 'applications']
        # The user can't change the status, can't change the creation time of the job,
        # and can't change his name or id
        read_only_fields = ['status', 'created_at', 'owner_name', 'owner_id']
