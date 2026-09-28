# CarWise Backend

Backend API for CarWise, a car-servicing marketplace app. Users manage their cars, find nearby workshops, book services, track service history and expenses, and receive push notifications about their bookings.

**Live API docs:** https://carwise.semanticsol.com/docs

## Tech Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.x (async, via asyncpg)
- **Migrations:** Alembic
- **Auth:** JWT (PyJWT) + Passlib/bcrypt for password hashing
- **Email:** Brevo (SMTP) via aiosmtplib
- **OAuth:** Google Sign-In (google-auth)
- **Push notifications:** OneSignal (REST API, called with httpx)
- **Production server:** Gunicorn (Uvicorn workers) under systemd, behind Nginx, HTTPS via Let's Encrypt (Certbot)
- **CI/CD:** GitHub Actions (deploys to AWS EC2 on push to `main`)

## Architecture

Every request flows through the same layers, in order:

```
Router → Schema (Pydantic) → Service → Unit of Work → Repository → Model
```

- **Router** — receives the HTTP request, delegates to a service
- **Schema** — validates the shape/format of incoming data
- **Service** — applies business rules and role-based authorization
- **Unit of Work** — opens one database transaction, holds all repositories
- **Repository** — runs the actual query for one specific table

Push notifications are sent from the service layer through FastAPI `BackgroundTasks`, so the API response is never delayed by, or dependent on, OneSignal.

## Roles

| Role | Access |
|---|---|
| **Customer** | Manages their own profile, cars, bookings, service history and expenses |
| **Workshop Staff** | Manages their own workshop's details, services, bookings and service history |
| **Admin** | Full system access, including approvals and broadcast notifications |

Account creation differs per role:
- **Customer** — self-registers via the mobile/web app, email OTP verification
- **Workshop Staff** — self-registers via `/auth/register-workshop`, account starts `pending_approval` until an Admin approves it (login is blocked until then)
- **Admin** — pre-seeded directly in the database (see `app/scripts/seed_admin.py`), never created via an API

## Features Implemented

### Auth Module
- Customer registration with OTP email verification
- OTP verify / resend (10-minute expiry, 60-second resend cooldown, 5-attempt lockout)
- Login (email + password), blocked for unverified or non-active accounts
- Google OAuth login (Sign in with Google)
- Forgot password → verify reset code → reset password
- Access + refresh token issuing, verification, and revocation (typed tokens — access and refresh cannot be used interchangeably)
- Logout (per-device session revocation)
- Workshop Staff self-registration (pending Admin approval)

### User Profile Module
- View own profile (`GET /users/me`)
- Edit profile — name, phone, location (`PUT /users/me`)
- Change password — old + new password, revokes all active sessions (`PUT /users/me/password`)
- Upload avatar — JPEG/PNG/WebP, 5MB max (`POST /users/me/avatar`)

### Cars Management Module
- Add a car (Customer, for themselves; Admin, for any user)
- List a user's cars (Customer sees their own; Staff/Admin specify `target_user_id`)
- Get car detail
- Update a car (owner, Workshop Staff, or Admin)
- Soft-delete a car (owner or Admin only — Staff cannot delete)
- Restore a soft-deleted car (blocked if its registration/engine number is now used by another active car)
- Associate an existing car with a different user account (Staff/Admin only)
- Duplicate prevention on registration number and engine number

### Admin Module
- Approve a pending Workshop Staff registration (`POST /admin/workshop-staff/{id}/approve`)
- Reject a pending Workshop Staff registration (`POST /admin/workshop-staff/{id}/reject`)

### Workshop / Service Management
- Service Categories (Admin-managed, shared across all workshops)
- Workshop self-management (details, hours, image) for staff
- Workshop Services (a workshop's priced offering of a category)
- Search with filters/sorting/pagination
- Nearby search with real distance (Haversine formula)

### Booking Management
- Create booking (car, workshop, one or more services, date/time); price is computed server-side and stored as a snapshot per service
- Full status lifecycle with valid-transition rules: Pending → Confirmed → In Progress → Completed, or Cancelled
- Cancel and Reschedule, both respecting business rules and working hours
- Each booking gets a unique booking reference (e.g. `BK-Z6RTRF`)
- No time-slot restriction — a workshop can take multiple simultaneous bookings; capacity is managed manually via the Workshop Panel

### Reviews & Ratings
- One review per completed booking (not per workshop) — enforced via a unique constraint on `booking_id`
- A workshop's average rating recalculates automatically on each new review

### Service History & Expenses
Each car has a history of everything spent on it. Entries come from two sources:

- **Automatic** — when a booking is marked **Completed**, a history entry is created from it (workshop name, total cost, service date). One entry per booking (unique on `booking_id`).
- **Manual expenses** — a customer can log their own expense for one of their cars (title, cost, date, optional details and workshop name). 

Rules and access:
- Expense cost must be greater than zero, and the service date cannot be in the future
- A customer can only add expenses to, and view history for, their own cars
- Workshop Staff can only view history generated from bookings at their own workshop
- Admin can view all entries
- All list endpoints are paginated (`page`, `page_size`, max 100), newest first

### Push Notifications (OneSignal)
- **Device registration** — a signed-in user registers a device token; multiple devices per user are supported. Registering a token that already exists re-activates it and reassigns it to the current user (e.g. someone else logs into the same phone). Tokens can be deactivated on logout.
- **Booking events** — a push is sent to the booking's owner when a booking is **created, confirmed, status-updated, cancelled, or rescheduled**. Notifications go only to the intended user, never to whoever performed the action.
- **Deep linking** — every payload carries a `type` and a `reference_id` (the booking id) so the mobile app can open the right screen.
- **Never blocks the request** — notifications are sent in the background; a OneSignal failure is logged and never fails the booking action.
- **Broadcasts (Admin only)** — send a promotional offer or system-maintenance notice to every active registered device (`promotional_offer` / `system_maintenance`). Unlike per-user notifications, a failed broadcast is reported back to the admin as an error.

Notification types: `booking_created`, `booking_confirmed`, `booking_status_updated`, `booking_cancelled`, `booking_rescheduled`, `promotional_offer`, `system_maintenance`. The types `service_reminder` and `new_chat_message` are defined but not used yet (see Next Steps).

## Project Structure

```
app/
├── api/v1/          # Routers (auth, users, cars, admin, service_categories, workshops,
│                    #          bookings, service_history, notifications)
├── core/            # Config, security, exceptions, dependencies, roles & notification types
├── db/              # Database engine/session setup
├── models/          # SQLAlchemy models (User, Car, Workshop, WorkshopService, ServiceCategory,
│                    #   Booking/BookingItem, WorkshopReview, ServiceHistory, DeviceToken,
│                    #   OtpCode, RefreshToken, SocialAccount)
├── repositories/    # Database query layer, one file per model
├── schema/          # Pydantic request/response schemas
├── service/         # Business logic, role-based authorization, notification_service
├── scripts/         # One-time scripts (e.g. seed_admin.py)
├── unit_of_work/    # Transaction wrapper tying repositories together
├── utils/           # Email sending, file storage, OTP generation, token hashing, booking references
├── tests/           # Automated test suite (in progress)
└── main.py          # App entrypoint
alembic/             # Database migrations
.github/workflows/   # deploy.yml — GitHub Actions deployment workflow
uploads/             # Uploaded files (avatars, workshop images) — not committed
logs/                # Application logs — not committed
```

## Setup (Local Development)

### 1. Clone and create a virtual environment
```bash
git clone https://github.com/FatimaFizaFatima/carwise-backend.git
cd carwise-backend
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root (it is git-ignored — never commit it):

```
APP_NAME=CarWise
APP_ENV=development
ALLOWED_ORIGINS=["http://localhost:5173"]

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/carwise
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your-brevo-smtp-login
SMTP_PASSWORD=your-brevo-smtp-key
SMTP_FROM=your-sender-email

ADMIN_EMAIL=admin@carwise.com
ADMIN_PASSWORD=a-strong-admin-password

ONESIGNAL_APP_ID=your-onesignal-app-id
ONESIGNAL_REST_API_KEY=your-onesignal-rest-api-key
```

Notes:
- Almost every variable is **required** — the app refuses to start if one is missing. Only `APP_NAME`, `APP_ENV` and `ALLOWED_ORIGINS` have defaults.
- `ALLOWED_ORIGINS` must be a **JSON array** (`["https://a.com","https://b.com"]`), not a comma-separated string. It controls which frontend domains browsers may call the API from (CORS).
- Use a different `SECRET_KEY` in production than in development.

### 4. Run database migrations
```bash
alembic upgrade head
```

### 5. Seed the Admin account (one time only)
```bash
python -m app.scripts.seed_admin
```

### 6. Start the server
```bash
uvicorn app.main:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

## API Endpoints

Routes are mounted at the root (there is no `/api/v1` prefix). Every endpoint except the Auth ones requires an `Authorization: Bearer <access_token>` header.

### Auth (`/auth`)
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a customer account, sends OTP via email |
| POST | `/auth/register-workshop` | Register as Workshop Staff (pending Admin approval) |
| POST | `/auth/verify-otp` | Verify email with OTP, returns tokens |
| POST | `/auth/resend-otp` | Resend OTP (rate-limited) |
| POST | `/auth/login` | Email + password login |
| POST | `/auth/oauth/google` | Google Sign-In |
| POST | `/auth/forgot-password` | Request a password reset code |
| POST | `/auth/verify-reset-code` | Verify reset code, returns a reset token |
| POST | `/auth/reset-password` | Set a new password using the reset token |
| POST | `/auth/refresh` | Exchange a refresh token for a new access token |
| POST | `/auth/logout` | Revoke the current refresh token |

### Users (`/users`)
| Method | Path | Description |
|---|---|---|
| GET | `/users/me` | Get the logged-in user's profile |
| PUT | `/users/me` | Update name, phone, or location |
| PUT | `/users/me/password` | Change password (requires current password) |
| POST | `/users/me/avatar` | Upload a profile photo |

### Cars (`/cars`)
| Method | Path | Description |
|---|---|---|
| POST | `/cars` | Add a car |
| GET | `/cars` | List a user's cars |
| GET | `/cars/{car_id}` | Get car detail |
| PUT | `/cars/{car_id}` | Update a car |
| DELETE | `/cars/{car_id}` | Soft-delete a car |
| POST | `/cars/{car_id}/restore` | Restore a soft-deleted car |
| POST | `/cars/{car_id}/associate` | Link a car to a different user account |

### Service Categories (`/service-categories`)
| Method | Path | Description |
|---|---|---|
| GET | `/service-categories` | List all categories |
| POST | `/service-categories` | Create a category (Admin) |
| DELETE | `/service-categories/{category_id}` | Delete a category (Admin) |

### Workshops (`/workshops`)
| Method | Path | Description |
|---|---|---|
| GET | `/workshops/me` | Get the staff member's own workshop |
| PUT | `/workshops/me` | Update own workshop details and hours |
| POST | `/workshops/me/image` | Upload a workshop image |
| GET | `/workshops/search` | Search with filters, sorting and pagination |
| GET | `/workshops/nearby` | Find nearby workshops with distance |
| GET | `/workshops/{workshop_id}` | Get workshop detail |
| GET | `/workshops/{workshop_id}/services` | List a workshop's services |
| POST | `/workshops/me/services` | Add a service to own workshop |
| DELETE | `/workshops/me/services/{service_id}` | Remove a service from own workshop |
| POST | `/workshops/{workshop_id}/reviews` | Review a workshop (after a completed booking) |
| GET | `/workshops/{workshop_id}/reviews` | List a workshop's reviews |

### Bookings (`/booking`)
| Method | Path | Description |
|---|---|---|
| POST | `/booking` | Create a booking |
| GET | `/booking` | List bookings (own for customers, workshop's for staff, all for admin) |
| GET | `/booking/{booking_id}` | Get booking detail |
| POST | `/booking/{booking_id}/cancel` | Cancel a booking |
| POST | `/booking/{booking_id}/reschedule` | Change the date/time |
| PATCH | `/booking/{booking_id}/status` | Move a booking through its lifecycle (Staff/Admin) |

### Service History & Expenses (`/history`)
| Method | Path | Description |
|---|---|---|
| POST | `/history` | Add a manual expense for one of your cars |
| GET | `/history/services` | Service history generated from completed bookings |
| GET | `/history/expenses` | Manually added expenses |
| GET | `/history/workshop` | History for the staff member's workshop (Staff) |
| GET | `/history/car/{car_id}` | Everything logged for one car |
| GET | `/history/{history_id}` | Single history entry detail |

### Notifications (`/notifications`)
| Method | Path | Description |
|---|---|---|
| POST | `/notifications/device-token` | Register or update a device's OneSignal subscription id (`device_type`: `ios`, `android` or `web`) |
| DELETE | `/notifications/device-token/{token}` | Unregister a device (e.g. on logout) |
| POST | `/notifications/broadcast` | Send a promotional/maintenance notification to all devices (Admin) |

### Admin (`/admin`)
| Method | Path | Description |
|---|---|---|
| POST | `/admin/workshop-staff/{user_id}/approve` | Approve a pending Workshop Staff account |
| POST | `/admin/workshop-staff/{user_id}/reject` | Reject a pending Workshop Staff account |

## Deployment

**Production setup:** a single AWS EC2 (Ubuntu) instance running PostgreSQL, the app, and Nginx.

- **App process:** Gunicorn with Uvicorn workers, managed by a systemd service named `carwise` (starts on boot, restarts on failure)
- **Reverse proxy:** Nginx forwards HTTPS traffic to the app on port 8000
- **HTTPS:** Let's Encrypt certificate via Certbot, auto-renewing
- **Configuration:** the production `.env` lives **only on the server**. It is never stored in GitHub.

### CI/CD (GitHub Actions)

`.github/workflows/deploy.yml` deploys automatically on every push or merge to `main` (it can also be run manually from the Actions tab). On each run it:

1. Connects to the server over SSH
2. Pulls the latest code from `main`
3. Installs dependencies (`pip install -r requirements.txt`)
4. Runs database migrations (`alembic upgrade head`)
5. Restarts the `carwise` service and checks it is active
6. Calls the public API (`/openapi.json`) and fails the run unless it returns HTTP 200
7. On failure, prints the last lines of the server log into the GitHub run

Progress and errors can be monitored from the repository's **Actions** tab.

**Required GitHub repository secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `EC2_HOST` | The server's hostname (no `https://`, no path) |
| `EC2_USER` | The SSH username (`ubuntu`) |
| `EC2_SSH_KEY` | Private SSH key that the workflow uses to log in to the server |

The server itself uses a read-only **deploy key** (added under the repo's Settings → Deploy keys) to pull the private repository.

### Manual operations on the server
```bash
sudo systemctl restart carwise      # restart the app
sudo systemctl status carwise       # check it is running
sudo journalctl -u carwise -f       # follow live logs
```

## Git Workflow

- `main` — stable, release-ready code. **Anything merged to `main` is deployed to production automatically.**
- `develop` — integration branch; all approved work lands here
- `feature/*` — one branch per piece of work, merged into `develop` via a reviewed pull request

Both `main` and `develop` are protected: no direct pushes, at least one approval required before merging. `main` only ever receives a pull request from `develop`, never from a feature branch directly.



