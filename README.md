# CarWise Backend

Backend API for CarWise, a car-servicing marketplace app. Users manage their cars, find nearby workshops, book services, and track service history.

This repository currently implements the **Authentication**, **User Profile**, **Cars Management**, and **Workshop Staff / Admin** modules.

## Tech Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.x (async, via asyncpg)
- **Migrations:** Alembic
- **Auth:** JWT (PyJWT) + Passlib/bcrypt for password hashing
- **Email:** Brevo (SMTP) via aiosmtplib
- **OAuth:** Google Sign-In (google-auth)

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

## Roles

| Role | Access |
|---|---|
| **Customer** | Manages their own profile, cars, and bookings |
| **Workshop Staff** | Manages their own workshop's details, services, and bookings |
| **Admin** | Full system access |

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
- Associate an existing car with a different user account (Staff/Admin only)
- Duplicate prevention on registration number and engine number

### Admin Module
- Approve a pending Workshop Staff registration (`POST /admin/workshop-staff/{id}/approve`)
- Reject a pending Workshop Staff registration (`POST /admin/workshop-staff/{id}/reject`)

## Project Structure

```
app/
├── api/v1/          # Routers (auth, users, cars, admin)
├── core/            # Config, security, exceptions, dependencies, roles
├── db/              # Database engine/session setup
├── models/          # SQLAlchemy models (User, Car, Workshop, OtpCode, RefreshToken, SocialAccount)
├── repositories/     # Database query layer, one file per model
├── schema/          # Pydantic request/response schemas
├── service/         # Business logic and role-based authorization
├── scripts/         # One-time scripts (e.g. seed_admin.py)
├── unit_of_work/    # Transaction wrapper tying repositories together
├── utils/           # Email sending, file storage, OTP generation, token hashing
├── tests/           # Automated test suite (in progress)
└── main.py          # App entrypoint
alembic/             # Database migrations
uploads/             # Uploaded files (avatars) — not committed
logs/                # Application logs — not committed
```

## Setup

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
Copy `.env.example` to `.env` and fill in real values:

```
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
```

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

### Auth (`/api/v1/auth`)
| Method | Path | Description |
|---|---|---|
| POST | `/register` | Create a customer account, sends OTP via email |
| POST | `/register-workshop` | Register as Workshop Staff (pending Admin approval) |
| POST | `/verify-otp` | Verify email with OTP, returns tokens |
| POST | `/resend-otp` | Resend OTP (rate-limited) |
| POST | `/login` | Email + password login |
| POST | `/oauth/google` | Google Sign-In |
| POST | `/forgot-password` | Request a password reset code |
| POST | `/verify-reset-code` | Verify reset code, returns a reset token |
| POST | `/reset-password` | Set a new password using the reset token |
| POST | `/refresh` | Exchange a refresh token for a new access token |
| POST | `/logout` | Revoke the current refresh token |

### Users (`/api/v1/users`)
| Method | Path | Description |
|---|---|---|
| GET | `/me` | Get the logged-in user's profile |
| PUT | `/me` | Update name, phone, or location |
| PUT | `/me/password` | Change password (requires current password) |
| POST | `/me/avatar` | Upload a profile photo |

### Cars (`/api/v1/cars`)
| Method | Path | Description |
|---|---|---|
| POST | `/` | Add a car |
| GET | `/` | List a user's cars |
| GET | `/{car_id}` | Get car detail |
| PUT | `/{car_id}` | Update a car |
| DELETE | `/{car_id}` | Soft-delete a car |
| POST | `/{car_id}/associate` | Link a car to a different user account |

### Admin (`/api/v1/admin`)
| Method | Path | Description |
|---|---|---|
| POST | `/workshop-staff/{user_id}/approve` | Approve a pending Workshop Staff account |
| POST | `/workshop-staff/{user_id}/reject` | Reject a pending Workshop Staff account |

## Git Workflow

- `main` — stable, release-ready code
- `develop` — integration branch; all approved work lands here
- `feature/*` — one branch per piece of work, merged into `develop` via a reviewed pull request

Both `main` and `develop` are protected: no direct pushes, at least one approval required before merging. `main` only ever receives a pull request from `develop`, never from a feature branch directly.

## Testing

Manually tested end-to-end (all endpoints, including failure cases: wrong passwords, expired/invalid OTPs, duplicate cars, invalid file types, token type mismatches, account status transitions, staff approval/rejection). An automated `pytest` suite is in progress (`app/tests/`).

## Known Limitations / Next Steps

- Avatar files are stored on local disk for now; migrating to an S3 bucket is planned alongside AWS deployment
- OTP delivery uses Brevo's free tier (300 emails/day, no custom domain yet)
- Workshop Staff permissions are not yet scoped to their own specific workshop (pending the full Workshop model, planned for the next ticket)
- Notifications and Home/Dashboard (Bookings, Services) are separate, upcoming modules