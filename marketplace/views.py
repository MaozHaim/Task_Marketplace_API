from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Job, Application
from .serializers import JobSerializer, ApplicationSerializer
import random


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


    def perform_create(self, serializer):
        # Fill 'owner' field automatically
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def hire(self, request, pk=None):
        """
        Hires a freelancer and closes the job using a thread-safe approach.
        This method uses `transaction.atomic` and `select_for_update` (row locking)
        to prevent race conditions when multiple users try to hire simultaneously.

        Body: { "application_id": <int> }
        Returns: 200 OK, 409 Conflict (if already hired), or error details.
        """
        # Extract application_id from the request and validate existence
        application_id = request.data.get('application_id')
        if not application_id:
            return Response(
                {"error": "application_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic(): # Atomic transaction
                job = Job.objects.select_for_update().get(pk=pk) # Lock the relevant job record
                if job.status != 'OPEN': # Make sure that the job is "open"
                    return Response(
                        {"error": "Job is already closed"},
                        status=status.HTTP_409_CONFLICT
                    )

                if job.owner == request.data.get('freelancer_id'):
                    return Response(
                        {"error": "A freelancer can't apply to his own jobs"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try: # Make sure that the application exists and that it is related to the job
                    application = Application.objects.select_for_update().get(
                        pk=application_id,
                        job=job
                    ) # Lock the relevant application record
                except Application.DoesNotExist: # application does not exist
                    return Response(
                        {"error": "Application not found for this job"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Update job record
                job.status = 'CLOSED'
                job.save()

                # Update application record
                application.is_hired = True
                application.save()

                # Simulation - sending an e-mail (by pushing to a Message Queue)
                simulate_queue_push(application_id)

                return Response({"status": "Hired successfully!"})

        except Job.DoesNotExist: # Job does not exist
            return Response({"error": "Job not found."}, status=status.HTTP_404_NOT_FOUND)
        except ConnectionError as e: # Failed to push to the Message Queue
            return Response(
                {"error": "Transaction rolled back: Could not reach notification service."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e: # General server error
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all().order_by('-submitted_at')
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


    def perform_create(self, serializer):
        # Fill 'freelancer' field automatically
        serializer.save(freelancer=self.request.user)


def simulate_queue_push(application_id):
    """
    Simulates pushing an e-mail request to a Message Queue.
    """
    if random.random() < 0.2: # 20% chance that the push failed
        raise ConnectionError("Failed to push message to Notification Queue")

    return True