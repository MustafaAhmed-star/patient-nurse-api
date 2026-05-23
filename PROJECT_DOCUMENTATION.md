# Ghaith Medical Services Platform API

Backend REST API for **غيث / Ghaith**, a medical home services platform connecting patients, nurses, and admins.

This project is backend-only. A Flutter frontend can consume these JSON APIs.

## 1. Technology Stack

- Python 3.12
- Django 5.2 LTS
- Django REST Framework
- PostgreSQL
- JWT authentication with Simple JWT
- django-environ for environment variables
- django-filter for filtering/searching
- django-cors-headers for Flutter/web client access
- drf-spectacular for OpenAPI documentation
- Pillow for uploaded image validation

## 2. Project Structure

```text
.
├── apps/
│   ├── accounts/        # User, nurse/patient profiles, auth, admin user APIs
│   ├── services/        # Medical services and areas
│   ├── orders/          # Orders, order items, ratings, lifecycle logic
│   └── notifications/   # In-app and email notification records
├── config/
│   ├── settings/        # Django settings using environment variables
│   ├── urls.py          # Main URL routing
│   ├── asgi.py
│   └── wsgi.py
├── shared/
│   ├── permissions/     # Reusable role and blocking permissions
│   ├── validators/      # Phone, name, password, file validators
│   ├── pagination/      # Standard paginated response format
│   ├── responses/       # Consistent JSON response envelope
│   └── services/        # Shared service namespace
├── tests/               # Focused API and validation tests
├── media/               # Uploaded files in development
├── manage.py
├── requirements.txt
├── .env.example
└── PROJECT_DOCUMENTATION.md
```

## 3. Response Format

All API responses use this shape:

```json
{
  "success": true,
  "message": "Order created successfully.",
  "data": {}
}
```

Validation and permission errors use the same envelope with `success: false`.

## 4. Language And RTL Readiness

The API is prepared for Arabic and English:

- Django i18n is enabled.
- Supported languages are `en` and `ar`.
- Clients can send `Accept-Language: ar` or `Accept-Language: en`.
- User-facing messages use Django translation helpers.
- Service and area names include both `name_en` and `name_ar`.
- Arabic is listed in `LANGUAGES_BIDI` for RTL-aware clients.

## 5. Models And Relationships

### User

Custom user model with UUID primary key.

Important fields:

- `email`: unique login field
- `role`: `ADMIN`, `NURSE`, `PATIENT`
- `is_blocked`: prevents protected API access

The same email cannot be reused across roles because email is globally unique.

### PatientProfile

One patient profile belongs to one user.

Important fields:

- `full_name`
- `phone`
- `address`
- `accepted_terms`

Patients must accept terms before registration.

### NurseProfile

One nurse profile belongs to one user.

Important fields:

- `full_name`
- `phone`
- `address`
- `gender`
- `wallet_number`
- `profile_image`
- `graduation_certificate`
- `syndicate_card`
- `interview_date`
- `is_approved`

Nurses cannot use nurse dashboard APIs until approved by admin.

### JoinRequest

Created automatically after nurse registration.

Statuses:

- `PENDING`
- `APPROVED`
- `REJECTED`

Admin approval updates both the join request and the nurse profile.

### Service

Medical service managed by admin.

Important fields:

- `name_en`
- `name_ar`
- `description_en`
- `description_ar`
- `price`
- `is_active`
- `is_deleted`

Delete is soft delete, so historical orders remain valid.

### Area

Geographic area managed by admin.

Important fields:

- `name_en`
- `name_ar`
- `transportation_fee`
- `is_active`
- `is_deleted`

### Order

Patient-created request for one or more services.

Important fields:

- `patient`
- `nurse`
- `area`
- `area_name_en`
- `area_name_ar`
- `address`
- `transportation_fee`
- `services_subtotal`
- `final_price`
- `status`

Prices are snapshotted at creation. Later service or area price changes do not affect existing orders.

### OrderItem

Snapshot of one service inside an order.

Important fields:

- `service`
- `service_name_en`
- `service_name_ar`
- `unit_price`
- `quantity`
- `total_price`

### Rating

Patient rating for a completed order.

Rules:

- one rating per order
- only the order patient can rate
- only completed orders can be rated
- score must be from 1 to 5

### Notification

Stores in-app notifications and tracks email sending.

Important fields:

- `recipient`
- `title`
- `message`
- `notification_type`
- `related_order`
- `related_join_request`
- `is_read`
- `email_sent`

## 6. Order Lifecycle

Statuses:

- `ACTIVE`: visible to approved nurses
- `PENDING`: admin-controlled review/reopen state
- `IN_PROGRESS`: assigned to one nurse and being handled
- `COMPLETED`: finished by nurse or admin
- `CANCELLED`: cancelled by admin

Normal nurse flow:

```text
ACTIVE -> IN_PROGRESS -> COMPLETED
```

If a nurse cancels an accepted order:

```text
IN_PROGRESS -> ACTIVE
```

Admin can:

- cancel any order
- move completed orders back to `PENDING`
- release `PENDING` orders to `ACTIVE`
- assign a nurse and move an order to `IN_PROGRESS`

## 7. Business Rules

- Patients can register and use the app immediately.
- Nurses register, create a join request, and wait for admin approval.
- Blocked users cannot access protected endpoints.
- Unapproved nurses cannot access nurse order APIs.
- Nurses cannot accept more than one `IN_PROGRESS` order at a time.
- Nurses cannot edit or delete orders.
- Patients cannot edit or delete orders.
- Admin has full management access.
- Nurse earnings equal the full final total of completed assigned orders.

## 8. Notifications

The project supports database notifications plus email notifications.

Notification events:

- nurse registration notifies admins
- nurse approval/rejection notifies the nurse
- patient order creation notifies admins
- nurse order acceptance notifies patient and admins
- order status changes notify affected patient, nurse, and admins
- rating submission notifies the nurse

Development email uses Django console email by default.

## 9. Main API Endpoints

All endpoints are prefixed with:

```text
/api/v1/
```

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/v1/auth/register/patient/` | Register patient |
| POST | `/api/v1/auth/register/nurse/` | Register nurse and create join request |
| POST | `/api/v1/auth/login/` | Login with email/password |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| GET/PATCH | `/api/v1/profile/` | Current user profile |

### Public Authenticated Lookups

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/services/` | List active services |
| GET | `/api/v1/areas/` | List active areas |

### Patient

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/patient/orders/` | List own orders |
| POST | `/api/v1/patient/orders/` | Create order |
| GET | `/api/v1/patient/orders/{id}/` | View own order |
| POST | `/api/v1/patient/orders/{id}/rate/` | Rate completed order |

### Nurse

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/nurse/orders/active/` | List active orders |
| GET | `/api/v1/nurse/orders/` | List active and assigned orders |
| POST | `/api/v1/nurse/orders/{id}/accept/` | Accept active order |
| POST | `/api/v1/nurse/orders/{id}/complete/` | Complete assigned order |
| POST | `/api/v1/nurse/orders/{id}/cancel/` | Return assigned order to active |
| GET | `/api/v1/nurse/orders/earnings/` | View earnings |
| GET | `/api/v1/nurse/orders/ratings/` | View received ratings |

### Notifications

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/notifications/` | List my notifications |
| GET | `/api/v1/notifications/unread-count/` | Count unread notifications |
| POST | `/api/v1/notifications/{id}/mark-read/` | Mark one as read |
| POST | `/api/v1/notifications/mark-all-read/` | Mark all as read |

### Admin

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/admin/nurses/` | List nurses |
| POST | `/api/v1/admin/nurses/{id}/approve/` | Approve nurse |
| POST | `/api/v1/admin/nurses/{id}/reject/` | Reject nurse |
| POST | `/api/v1/admin/nurses/{id}/block/` | Block/unblock nurse |
| GET | `/api/v1/admin/patients/` | List patients |
| POST | `/api/v1/admin/patients/{id}/block/` | Block/unblock patient |
| GET | `/api/v1/admin/join-requests/` | List join requests |
| POST | `/api/v1/admin/join-requests/{id}/approve/` | Approve join request |
| POST | `/api/v1/admin/join-requests/{id}/reject/` | Reject join request |
| CRUD | `/api/v1/admin/services/` | Manage services |
| CRUD | `/api/v1/admin/areas/` | Manage areas |
| GET/PATCH | `/api/v1/admin/orders/` | Manage orders |
| POST | `/api/v1/admin/orders/{id}/change-status/` | Change order status |
| POST | `/api/v1/admin/orders/{id}/cancel/` | Cancel order |
| GET | `/api/v1/admin/notifications/` | View all notifications |

OpenAPI schema:

```text
/api/v1/schema/
/api/v1/docs/
```

## 10. Setup Instructions

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create environment file

```bash
cp .env.example .env
```

Update `.env` with your real PostgreSQL credentials.

### 4. Create PostgreSQL database

Example:

```bash
createdb ghaith_db
createuser ghaith_user
```

Then grant the user permissions according to your PostgreSQL setup.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create admin user

```bash
python manage.py createsuperuser
```

The superuser automatically uses the `ADMIN` role.

### 7. Run development server

```bash
python manage.py runserver
```

Server URL:

```text
http://127.0.0.1:8000/
```

## 11. Environment Variables

| Variable | Description |
| --- | --- |
| `DEBUG` | Development debug mode |
| `SECRET_KEY` | Django secret key |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `DATABASE_URL` | PostgreSQL database URL |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token lifetime |
| `REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token lifetime |
| `EMAIL_BACKEND` | Email backend |
| `EMAIL_HOST` | SMTP host |
| `EMAIL_PORT` | SMTP port |
| `EMAIL_USE_TLS` | SMTP TLS flag |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `DEFAULT_FROM_EMAIL` | Sender email |
| `MAX_UPLOAD_SIZE_MB` | Max upload size |

## 12. Example Requests

### Register Patient

```http
POST /api/v1/auth/register/patient/
Content-Type: application/json
Accept-Language: en
```

```json
{
  "full_name": "Ahmed Ali",
  "phone": "01012345678",
  "email": "patient@example.com",
  "address": "Cairo",
  "password": "Strong!123",
  "accepted_terms": true
}
```

Example response:

```json
{
  "success": true,
  "message": "Patient registered successfully.",
  "data": {
    "email": "patient@example.com",
    "full_name": "Ahmed Ali",
    "phone": "01012345678",
    "address": "Cairo",
    "accepted_terms": true
  }
}
```

### Login

```http
POST /api/v1/auth/login/
Content-Type: application/json
```

```json
{
  "email": "patient@example.com",
  "password": "Strong!123"
}
```

Example response:

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "refresh": "refresh-token",
    "access": "access-token",
    "user": {
      "email": "patient@example.com",
      "role": "PATIENT"
    }
  }
}
```

### Create Order

```http
POST /api/v1/patient/orders/
Authorization: Bearer access-token
Content-Type: application/json
```

```json
{
  "area_id": "area-uuid",
  "address": "Apartment 10, Cairo",
  "services": [
    {
      "service_id": "service-uuid",
      "quantity": 2
    }
  ]
}
```

Example response:

```json
{
  "success": true,
  "message": "Order created successfully.",
  "data": {
    "status": "ACTIVE",
    "transportation_fee": "25.00",
    "services_subtotal": "200.00",
    "final_price": "225.00"
  }
}
```

### Nurse Accepts Order

```http
POST /api/v1/nurse/orders/{order_id}/accept/
Authorization: Bearer nurse-access-token
```

Example response:

```json
{
  "success": true,
  "message": "Order accepted successfully.",
  "data": {
    "status": "IN_PROGRESS"
  }
}
```

### Mark Notification As Read

```http
POST /api/v1/notifications/{notification_id}/mark-read/
Authorization: Bearer access-token
```

Example response:

```json
{
  "success": true,
  "message": "Notification marked as read.",
  "data": {
    "is_read": true
  }
}
```

## 13. Running Tests

The app is PostgreSQL-ready. For quick local logic tests without creating PostgreSQL credentials, you can temporarily override `DATABASE_URL`:

```bash
DATABASE_URL=sqlite:////tmp/ghaith_test.sqlite3 python manage.py test
```

For production-like testing, create the PostgreSQL database and run:

```bash
python manage.py test
```

## 14. Notes For Flutter

- Send JWT access token in `Authorization: Bearer <token>`.
- Use `Accept-Language: ar` for Arabic responses.
- Use multipart form data for nurse registration because it includes file uploads.
- Use paginated `data.results` for list screens.
- Keep IDs as strings because UUIDs are returned in JSON.
