# Task Marketplace API
A Backend API for a freelance marketplace, built with Django REST Framework (DRF). This project focuses on data integrity, concurrency management (handling Race Conditions), and system reliability.

# Project Overview & Workflow
The system facilitates a hiring process between Job Owners and Freelancers.

# The Flow:
Job Creation: An Owner posts a new Job (Title, Description).
Endpoint: POST /marketplace/jobs/

Application: A Freelancer applies for the job with a bid price.
Validation: Users cannot apply to their own jobs.
Endpoint: POST /marketplace/applications/

Hiring: The Owner selects an application and hires the freelancer.
Validation: Only the job owner can perform this action.
Outcome: The Job status becomes CLOSED, the Application is marked as hired, and a notification is sent.
Endpoint: POST /marketplace/jobs/{id}/hire/

# Installation & Setup
Prerequisites
Python 3.8+
pip (Python package installer)

1. Clone & Environment Setup
(Bash)

Clone the repository -
git clone <your-repo-link>
cd marketplace

Create a virtual environment -
python -m venv venv

Activate the environment
On Windows:
venv\Scripts\activate
On Mac/Linux:
source venv/bin/activate

2. Install Dependencies
(Bash)
pip install django djangorestframework pytest pytest-django

3. Database Setup
4. Initialize the SQLite database and apply migrations:
(Bash)
python manage.py migrate

5. Create Users (Crucial for testing)
Since the system relies on authentication (Owners vs Freelancers), create a superuser to access the Admin panel and API:
(Bash)
python manage.py createsuperuser

6. Run the Server
(Bash)
python manage.py runserver
Access the API at: http://127.0.0.1:8000/marketplace/jobs/

# Engineering Architecture
1. Handling Race Conditions (The "Hire" Logic)
The Challenge: Multiple requests trying to "hire" different freelancers for the same job simultaneously could lead to a job being closed twice or data corruption.
The Solution: Locking using select_for_update() within an atomic transaction.
Mechanism: When a hire request begins, the database locks the specific Job row.
Effect: Any concurrent request trying to modify this job will pause and wait until the first transaction finishes.
Result: The second request will see that the job status is already CLOSED and will fail gracefully with 409 Conflict.
Note: While implemented here on SQLite, this locking mechanism is most effective on production databases like PostgreSQL.

2. System Reliability (The Bonus Task)
The Challenge: The system needs to notify the freelancer (simulated via a Message Queue) upon hiring. What happens if the DB updates succeed, but the notification fails?

The Decision: Strong Consistency (Rollback) I chose a Rollback Policy to prevent "Zombie States" (where a user is hired in the DB but was never notified).

Implementation: The notification function (simulate_queue_push) is called inside the transaction.atomic() block.

Outcome: If the external service fails (raises an Exception), the entire database transaction is rolled back. The Job remains OPEN and the Application remains not hired.

📂 File Structure Guide
models.py: Defines the Job and Application schemas.

Key detail: Uses related_name (e.g., posted_jobs, applications) to allow intuitive reverse lookups and cleaner Serializers.

views.py: Contains the business logic.

Implements the hire custom action.

Enforces permissions (Owner vs. Freelancer).

Manages Atomic Transactions and Locking.

serializers.py: Handles data validation and JSON conversion.

Includes Nested Serialization to display applications within job details.

tests.py: A comprehensive test suite using pytest.

Covers: Happy paths, Race conditions, Permission logic, and Transaction rollbacks.

✅ Running Tests
The project includes a full test suite covering edge cases and concurrency logic.

Bash
# Run all tests
pytest

# Run with output logs
pytest -s
Test Coverage Highlights:
test_hire_success: Verifies full flow (Owner hires freelancer).

test_hire_job_already_closed: Ensures 409 Conflict on double booking.

test_create_application_owner_cannot_apply: Prevents owners from applying to their own jobs (403 Forbidden).

test_hire_rollback_on_email_failure: Verifies DB rollback when the notification service is down.
