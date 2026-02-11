# Task Marketplace API

A simple Backend API for a freelance marketplace, built with Django REST Framework (DRF).
This project focuses on data integrity, concurrency management (handling Race Conditions), and system reliability.

---

## Project Overview & Workflow

The system facilitates a hiring process between **Job Owners** and **Freelancers**.

### The Flow:

1.  **Job Creation**
    * An **Owner** posts a new Job (Title, Description).
    * Endpoint: `POST /marketplace/jobs/`

2.  **Application**
    * A **Freelancer** applies for the job with a bid price.
    * Validation: Users cannot apply to their own jobs.
    * Endpoint: `POST /marketplace/applications/`

3.  **Hiring**
    * The **Owner** selects an application and hires the freelancer.
    * Validation: Only the job owner can perform this action.
    * Outcome: The Job status becomes `CLOSED`, the Application is marked as `hired`, and a notification is sent.
    * Endpoint: `POST /marketplace/jobs/{id}/hire/`

### File Structure Guide
   * models.py: Defines the Job and Application schemas.
   * views.py: Contains the business logic, implements the hire custom action, enforces permissions (Owner vs. Freelancer) and manages Atomic Transactions and Locking.
   * serializers.py: Handles data validation and JSON conversion, includes Nested Serialization to display applications within job details.
   * tests.py: A comprehensive test suite using pytest. Covers: Happy path, Race condition logic, Permission logic, and Transaction rollbacks.

---

## Installation & Setup

### 0. Prerequisites
* Python 3.8+
* pip (Python package installer)

### 1. Clone & Environment Setup
1.1. **Clone the repository**
   * `git clone <your-repo-link>`
   * `cd marketplace`

1.2. **Create a virtual environment**
   * `python -m venv venv`

1.3. **Activate the environment**
   * On Windows: `venv\Scripts\activate`
   * On Mac/Linux: `source venv/bin/activate`

### 2. Install Dependencies
   * `pip install django djangorestframework pytest pytest-django`

### 3. Database Setup
Initialize the SQLite database and apply migrations -
   * `python manage.py migrate`

### 4. Create Users (Crucial for testing)
Since the system relies on authentication (Owners vs Freelancers), create a superuser to access the Admin panel and API:
   * `python manage.py createsuperuser`

### 5. Run the Server
   * `python manage.py runserver`
   * Access the API at: http://127.0.0.1:8000/marketplace/jobs/

---

## Engineering Architecture
### 1. Handling Race Conditions (The "Hire" Logic)
   * The Challenge: Multiple requests trying to "hire" different freelancers for the same job simultaneously could lead to a job being closed twice or data corruption.
   * The Solution: Locking using select_for_update() within an atomic transaction.
   * Mechanism: When a hire request begins, the database locks the specific Job row.
   * Effect: Any concurrent request trying to modify this job will pause and wait until the first transaction finishes.
   * Result: The second request will see that the job status is already CLOSED and will fail gracefully with 409 Conflict.

Note: While implemented here on SQLite, this locking mechanism is most effective on production databases like PostgreSQL.

### 2. System Reliability (The Bonus Task)
   * The Challenge: The system needs to notify the freelancer (simulated via a Message Queue) upon hiring. What happens if the DB updates succeed, but the notification fails?
   * The Decision: Strong Consistency (Rollback) I chose a Rollback Policy to prevent "Zombie States" (where a user is hired in the DB but was never notified).
   * Implementation: The notification function (simulate_queue_push) is called inside the transaction.atomic() block.
   * Outcome: If the external service fails (raises an Exception), the entire database transaction is rolled back. The Job remains OPEN and the Application remains not hired.
