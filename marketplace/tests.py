import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from .models import Job, Application
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_data(db):
    # Create owner-user
    owner_user = User.objects.create_user(username='boss_man', password='password')

    # Create freelancer-user
    freelancer_user = User.objects.create_user(username='python_dev', password='password')

    # Create job
    job = Job.objects.create(
        title="Test Job",
        description="Test Desc",
        owner=owner_user,
        status='OPEN'
    )

    # Create application
    application = Application.objects.create(
        job=job,
        freelancer=freelancer_user,
        bid_price=100.00
    )

    return owner_user, freelancer_user, job, application


@pytest.mark.django_db
class TestHiringProcess:

    def test_hire_success(self, api_client, create_data):
        """
        Test: Successful update.
        Validate that in the end of the process: 'status' == CLOSED, 'is_hired' == True
        and response.status_code == status.HTTP_200_OK.
        """
        owner, _, job, application = create_data
        api_client.force_authenticate(user=owner)

        url = reverse('job-hire', args=[job.id])
        with patch('marketplace.views.simulate_queue_push') as mock_email:
            mock_email.return_value = True
            response = api_client.post(url, {'application_id': application.id}, format='json')

        if response.status_code != 200:
            print(f"\nERROR DEBUG: {response.status_code} - {response.data}")
        assert response.status_code == status.HTTP_200_OK

        job.refresh_from_db()
        application.refresh_from_db()
        assert job.status == 'CLOSED'
        assert application.is_hired is True


    def test_hire_job_already_closed(self, api_client, create_data):
        """
        Test: Prevention of hiring for a closed job (Race Condition logic).
        Validate that response.status_code == status.HTTP_409_CONFLICT.
        """
        owner, _, job, application = create_data
        api_client.force_authenticate(user=owner)

        # Close manually
        job.status = 'CLOSED'
        job.save()

        url = reverse('job-hire', args=[job.id]) # Creates /jobs/1/hire/
        response = api_client.post(url, {'application_id': application.id}, format='json')

        assert response.status_code == status.HTTP_409_CONFLICT


    def test_hire_job_not_found(self, api_client, create_data):
        """
        Test: Attempt to hire for a non-existent job ID.
        Validate that response.status_code == status.HTTP_404_NOT_FOUND.
        """
        owner, _, _, application = create_data
        api_client.force_authenticate(user=owner)

        non_existent_job_id = 99999
        url = reverse('job-hire', args=[non_existent_job_id]) # Creates /jobs/1/hire/
        response = api_client.post(url, {'application_id': application.id}, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_hire_application_not_found(self, api_client, create_data):
        """
        Test: Attempt to hire with a non-existent application ID.
        Validate that response.status_code == status.HTTP_404_NOT_FOUND.
        """
        owner, _, job, _ = create_data
        api_client.force_authenticate(user=owner)

        url = reverse('job-hire', args=[job.id]) # Creates /jobs/1/hire/
        response = api_client.post(url, {'application_id': 88888}, format='json') # non-existent application_id

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_hire_application_mismatch(self, api_client, create_data):
        """
        Test: Application mismatch (Application belongs to a different job).
        Validate that response.status_code == status.HTTP_404_NOT_FOUND.
        """
        owner, _, job1, application1 = create_data
        api_client.force_authenticate(user=owner)

        job2 = Job.objects.create(
            title="Another Job",
            owner=owner,
            status='OPEN'
        )

        # Try to hire application1 (related to job1) for job2
        url = reverse('job-hire', args=[job2.id]) # Creates /jobs/2/hire/
        response = api_client.post(url, {'application_id': application1.id}, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND


    def test_create_application_owner_cannot_apply(self, api_client, create_data):
        """
        Test: Owner attempts to apply for their own job.
        Validate that response.status_code == status.HTTP_403_FORBIDDEN.
        """
        owner, _, job, _ = create_data
        api_client.force_authenticate(user=owner)

        url = reverse('application-list')
        response = api_client.post(url, {
            'job': job.id,
            'bid_price': 100
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_hire_missing_application_id(self, api_client, create_data):
        """
        Test: Missing 'application_id' in request body.
        Validate that response.status_code == status.HTTP_400_BAD_REQUEST.
        """
        owner, _, job, _ = create_data
        api_client.force_authenticate(user=owner)

        url = reverse('job-hire', args=[job.id])
        response = api_client.post(url, {'wrong_field': 123}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


    def test_hire_rollback_on_email_failure(self, api_client, create_data):
        """
        Test: Transaction Rollback on external failure (Reliability/Bonus).
        Validate that response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE,
        and DB state reverts: 'status' == OPEN, 'is_hired' == False.
        """
        owner, _, job, application = create_data
        api_client.force_authenticate(user=owner)

        url = reverse('job-hire', args=[job.id])

        # In this test, the e-mail simulation function will always raise a ConnectionError
        with patch('marketplace.views.simulate_queue_push') as mock_email:
            mock_email.side_effect = ConnectionError("Queue is down!")
            response = api_client.post(url, {'application_id': application.id}, format='json')

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        job.refresh_from_db()
        application.refresh_from_db()

        assert job.status == 'OPEN'
        assert application.is_hired is False