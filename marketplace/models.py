from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):
    # Auto pk
    # Each job is related to an owner (valid user)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='OPEN')

    def __str__(self):
        return f"{self.title}, offered by {self.owner.username} (Status: {self.status})"


class Application(models.Model):
    # Auto pk
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    freelancer_name = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications_submitted')
    bid_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_hired = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application by {self.freelancer.username} for {self.job.title}"