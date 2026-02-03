# BIU Dormitory Exchange Platform

A backend API for Bar-Ilan University students to transfer dorm leases and swap room categories. Built with FastAPI, Firestore, and Firebase Auth, designed to run entirely on the GCP free tier.

## What It Solves

**1. Lease Transfer (Exit Problem)**
A student leaves before their 12-month lease ends and needs to transfer the remaining contract months to another student.

**2. Category Swap (Upgrade Problem)**
A student in Dorm Category A wants to move to Category B. They must simultaneously find a replacement for their current room AND secure a vacancy in the target category. This platform handles the two-sided matching atomically.

---

## Architecture

```
┌─────────────┐     Firebase ID Token     ┌──────────────────────┐
│   Frontend   │ ────────────────────────> │  FastAPI (Cloud Run) │
│   (SPA)      │ <──────────────────────── │                      │
└─────────────┘      JSON responses        │  ┌────────────────┐  │
                                           │  │ Auth Middleware │  │
                                           │  │ (Firebase Admin)│  │
                                           │  └───────┬────────┘  │
                                           │          │           │
                                           │  ┌───────▼────────┐  │
                                           │  │ Route Handlers  │  │
                                           │  └───────┬────────┘  │
                                           │          │           │
                                           │  ┌───────▼────────┐  │
                                           │  │ Service Layer   │  │
                                           │  │ (State Machine  │  │
                                           │  │  + Matching     │  │
                                           │  │  + Transactions)│  │
                                           │  └───────┬────────┘  │
                                           └──────────┼───────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │   Firestore    │
                                              │   (Native)     │
                                              └────────────────┘
```

**Stack:** Python 3.13 · FastAPI · Google Cloud Firestore · Firebase Auth · Cloud Run

---

## Project Structure

```
app/
├── main.py                        # FastAPI app creation, CORS, router registration
├── config.py                      # Environment settings (pydantic-settings)
├── auth/
│   ├── dependencies.py            # Firebase token verification (FastAPI dependency)
│   └── models.py                  # FirebaseUser model
├── models/
│   ├── enums.py                   # RoomCategory, ListingType, status enums
│   ├── user.py                    # User profile models
│   ├── room.py                    # Room models
│   ├── listing.py                 # Lease transfer & swap request models
│   ├── match.py                   # Match response model
│   └── transaction.py             # Transaction response model
├── services/
│   ├── firestore_client.py        # Firestore async client singleton
│   ├── user_service.py            # User CRUD operations
│   ├── room_service.py            # Room CRUD operations
│   ├── listing_service.py         # Listing CRUD, claim, cancel (with Firestore txns)
│   ├── match_service.py           # Match accept/reject (with Firestore txns)
│   ├── transaction_service.py     # Transaction confirm/cancel (atomic room swaps)
│   └── matching_engine.py         # Compatibility matching for transfers and swaps
├── state_machine/
│   ├── listing_states.py          # LeaseTransfer state transitions
│   ├── swap_states.py             # SwapRequest state transitions
│   └── transitions.py             # Unified transition validator
├── routes/
│   ├── health.py                  # GET /health
│   ├── users.py                   # User profile endpoints
│   ├── rooms.py                   # Room endpoints
│   ├── listings.py                # Listing endpoints
│   ├── matches.py                 # Match endpoints
│   └── transactions.py            # Transaction endpoints
└── middleware/
    └── error_handler.py           # Global exception classes and handlers

tests/
├── conftest.py                    # Fixtures: mock Firestore, test users, async client
├── test_state_machine.py          # State transition validation (37 tests)
├── test_matching_engine.py        # Date overlap, swap compatibility (17 tests)
├── test_routes_users.py           # User + health endpoints (7 tests)
├── test_routes_listings.py        # Listing CRUD + filters (14 tests)
├── test_routes_matches.py         # Match get/filter (4 tests)
├── test_transactions.py           # Transaction get/cancel (5 tests)
└── test_concurrency.py            # Concurrency guard verification (6 tests)
```

---

## Prerequisites

- **Python 3.13** (tested with 3.13.11)
- **GCP Project** with Firestore and Firebase Auth enabled
- **Firebase service account key** (for local development)

---

## Local Development Setup

### 1. Clone and create virtual environment

```bash
git clone <your-repo-url>
cd Flat-Matching-for-Dormitories.

python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Set up GCP project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud config set project barilan-exchange

# Enable required APIs
gcloud services enable firestore.googleapis.com
gcloud services enable identitytoolkit.googleapis.com

# Create Firestore database (if not exists)
gcloud firestore databases create --location=nam5
```

### 3. Create a Firebase service account key

1. Go to [Firebase Console](https://console.firebase.google.com/) → your project → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save the file as `service-account.json` in the project root (it's gitignored)

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
PROJECT_ID=barilan-exchange
ENVIRONMENT=development
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
CORS_ORIGINS=["http://localhost:3000"]
MATCH_EXPIRY_HOURS=48
LISTING_EXPIRY_DAYS=30
```

### 5. Run the server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 6. Run tests

```bash
source .venv/bin/activate
pytest
```

All 90 tests should pass. Tests use mocked Firestore — no live database needed.

---

## Deploy to GCP Cloud Run

### 1. Set your project

```bash
gcloud config set project barilan-exchange
```

### 2. Deploy

```bash
gcloud run deploy biu-dorm-exchange \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 60 \
  --set-env-vars "ENVIRONMENT=production,PROJECT_ID=barilan-exchange"
```

service-url:  https://biu-dorm-exchange-nlt4ri4bza-uc.a.run.app

This builds the Docker image via Cloud Build and deploys to Cloud Run. No `GOOGLE_APPLICATION_CREDENTIALS` is needed in production — Cloud Run provides credentials automatically.

### 3. Deploy Firestore indexes

```bash
gcloud firestore indexes composite create \
  --collection-group=listings \
  --field-config field-path=listing_type,order=ascending \
  --field-config field-path=status,order=ascending \
  --field-config field-path=room_category,order=ascending \
  --field-config field-path=lease_start_date,order=ascending
```

Or deploy all indexes at once using the Firebase CLI:

```bash
npm install -g firebase-tools
firebase login
firebase init firestore   # select your project
# Copy firestore.indexes.json into the firebase directory
firebase deploy --only firestore:indexes
```

### 4. Get your service URL

```bash
gcloud run services describe biu-dorm-exchange \
  --region us-central1 \
  --format="value(status.url)"
```

---

## Authentication

All endpoints except `GET /health` require a Firebase Auth ID token.

### How it works

1. Your frontend authenticates users with Firebase Auth (email/password, Google sign-in, etc.)
2. Firebase returns a JWT ID token
3. Include it in every API request:

```
Authorization: Bearer <firebase-id-token>
```

### Getting a token for testing

Use the Firebase Auth REST API:

```bash
# Sign up a test user
curl -X POST \
  "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=<FIREBASE_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@biu.ac.il","password":"testpass123","returnSecureToken":true}'

# Sign in and get token
curl -X POST \
  "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=<FIREBASE_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@biu.ac.il","password":"testpass123","returnSecureToken":true}'
```

The `idToken` field in the response is your Bearer token.

---

## API Reference

Base URL: `http://localhost:8000` (local) or your Cloud Run URL (production).

All authenticated endpoints require: `Authorization: Bearer <token>`

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Health check |

### Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/users/profile` | Yes | Create your profile |
| `GET` | `/api/v1/users/me` | Yes | Get your profile |
| `PUT` | `/api/v1/users/me` | Yes | Update your profile |
| `GET` | `/api/v1/users/{uid}` | Yes | Get another user's public profile |

**Create profile:**
```bash
curl -X POST http://localhost:8000/api/v1/users/profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Yael Cohen",
    "student_id": "211234567",
    "phone": "+972501234567",
    "current_room_id": null
  }'
```

### Rooms

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/rooms` | Yes | Register a room |
| `GET` | `/api/v1/rooms` | Yes | List rooms (filter: `?category=A&building=Building+3`) |
| `GET` | `/api/v1/rooms/{room_id}` | Yes | Get room details |
| `PUT` | `/api/v1/rooms/{room_id}` | Yes | Update room |

**Register a room:**
```bash
curl -X POST http://localhost:8000/api/v1/rooms \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "building": "Building 3",
    "floor": 2,
    "room_number": "204",
    "category": "A",
    "description": "2-person room with balcony",
    "amenities": ["air_conditioning", "balcony"]
  }'
```

### Listings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/listings/lease-transfer` | Yes | Create a lease transfer listing |
| `POST` | `/api/v1/listings/swap-request` | Yes | Create a swap request listing |
| `GET` | `/api/v1/listings` | Yes | Browse listings (filter: `?type=LEASE_TRANSFER&category=A&status=OPEN&building=...`) |
| `GET` | `/api/v1/listings/my` | Yes | Get your own listings |
| `GET` | `/api/v1/listings/{id}` | Yes | Get listing details |
| `PUT` | `/api/v1/listings/{id}` | Yes | Update your listing (OPEN only) |
| `POST` | `/api/v1/listings/{id}/cancel` | Yes | Cancel your listing |
| `POST` | `/api/v1/listings/{id}/claim` | Yes | Claim a listing (create match proposal) |
| `GET` | `/api/v1/listings/{id}/compatible` | Yes | Find compatible swap partners |

**Create lease transfer:**
```bash
curl -X POST http://localhost:8000/api/v1/listings/lease-transfer \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "<room-id>",
    "lease_start_date": "2026-03-01",
    "lease_end_date": "2026-08-31",
    "description": "Nice room, available immediately",
    "asking_price": 500
  }'
```

**Create swap request:**
```bash
curl -X POST http://localhost:8000/api/v1/listings/swap-request \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "<room-id>",
    "lease_start_date": "2026-03-01",
    "lease_end_date": "2026-08-31",
    "description": "Want to upgrade to category B",
    "desired_categories": ["B"],
    "desired_buildings": ["Building 5"]
  }'
```

**Claim a lease transfer:**
```bash
curl -X POST http://localhost:8000/api/v1/listings/<listing-id>/claim \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am interested in this room"}'
```

**Claim a swap (provide your listing ID):**
```bash
curl -X POST http://localhost:8000/api/v1/listings/<their-listing-id>/claim \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"claimant_listing_id": "<your-listing-id>"}'
```

### Matches

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/matches/my` | Yes | Get your matches (filter: `?status=PROPOSED`) |
| `GET` | `/api/v1/matches/{id}` | Yes | Get match details |
| `POST` | `/api/v1/matches/{id}/accept` | Yes | Accept a match (listing owner only) |
| `POST` | `/api/v1/matches/{id}/reject` | Yes | Reject a match (listing owner only) |

### Transactions

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/transactions/my` | Yes | Get your transactions (filter: `?status=COMPLETED`) |
| `GET` | `/api/v1/transactions/{id}` | Yes | Get transaction details |
| `POST` | `/api/v1/transactions/{id}/confirm` | Yes | Confirm and execute the transfer/swap |
| `POST` | `/api/v1/transactions/{id}/cancel` | Yes | Cancel a pending transaction |

---

## Lifecycle Flows

### Lease Transfer Flow

```
Student A creates listing ──> OPEN
                                │
Student B claims listing ─────> MATCHED
                                │
Student A accepts match ──────> PENDING_APPROVAL
                                │       │
Student A confirms ──────────> COMPLETED │
  (room occupant updated         └────> CANCELLED
   atomically in Firestore)              (either party)
```

1. **Student A** creates a lease transfer listing for their room with date range and optional price
2. **Student B** browses open listings and claims one — a match proposal is created
3. **Student A** reviews the match and accepts or rejects it
4. On accept: a transaction is created. Either party confirms to execute it
5. On confirm: room occupancy is updated atomically (Firestore transaction)

### Swap Flow

```
Student A creates swap ──────> OPEN
Student B creates swap ──────> OPEN
                                │
B claims A's listing ─────────> FULLY_MATCHED (both listings)
  (with their listing ID)       │
                                │
Both parties accept ──────────> PENDING_APPROVAL
                                │
Confirm ─────────────────────> COMPLETED
  (both rooms swap occupants     (atomic Firestore transaction)
   atomically)
```

1. **Student A** (Category A, wants B) creates a swap request
2. **Student B** (Category B, wants A) creates a swap request
3. Either student finds the other via `GET /listings/{id}/compatible`
4. One claims the other's listing, providing their own listing ID — both move to `FULLY_MATCHED`
5. Both parties accept their respective matches
6. On confirm: both rooms swap occupants atomically

---

## State Machines

### Lease Transfer States

| State | Description | Next States |
|-------|-------------|-------------|
| `OPEN` | Listing is active and visible | `MATCHED`, `CANCELLED`, `EXPIRED` |
| `MATCHED` | Someone has claimed this listing | `PENDING_APPROVAL`, `OPEN` (reject), `CANCELLED` |
| `PENDING_APPROVAL` | Match accepted, awaiting confirmation | `COMPLETED`, `CANCELLED` |
| `COMPLETED` | Transfer executed (terminal) | — |
| `CANCELLED` | Cancelled by owner (terminal) | — |
| `EXPIRED` | Listing expired (terminal) | — |

### Swap Request States

| State | Description | Next States |
|-------|-------------|-------------|
| `OPEN` | Listing is active | `PARTIAL_MATCH`, `FULLY_MATCHED`, `CANCELLED`, `EXPIRED` |
| `PARTIAL_MATCH` | One side of the swap is resolved | `FULLY_MATCHED`, `OPEN` (reject), `CANCELLED`, `EXPIRED` |
| `FULLY_MATCHED` | Both sides resolved | `PENDING_APPROVAL`, `PARTIAL_MATCH` (one fails), `CANCELLED` |
| `PENDING_APPROVAL` | All matches accepted | `COMPLETED`, `CANCELLED` |
| `COMPLETED` | Swap executed (terminal) | — |
| `CANCELLED` | Cancelled (terminal) | — |
| `EXPIRED` | Expired (terminal) | — |

---

## Firestore Data Model

### Collections

| Collection | Document ID | Purpose |
|-----------|------------|---------|
| `users` | Firebase UID | Student profiles |
| `rooms` | Auto-generated | Dorm rooms with category/building |
| `listings` | Auto-generated | Lease transfers and swap requests |
| `matches` | Auto-generated | Match proposals between users |
| `transactions` | Auto-generated | Executed transfers/swaps |

### Key Design Decisions

- **Single `listings` collection** with a `listing_type` discriminator field — avoids cross-collection joins
- **Denormalized `room_category` and `room_building`** on listings — eliminates N+1 reads when browsing
- **`version` field** on mutable documents — optimistic concurrency control
- **One active listing per user** — prevents conflicting matches
- **48-hour match expiry** — prevents stale matches from blocking listings
- **Lazy expiration** — listings checked on read instead of requiring a scheduled job

---

## Concurrency Safety

All critical operations use **Firestore transactions** to prevent race conditions:

- **Claiming a listing**: Read listing status → verify OPEN → create match → update status (atomic)
- **Swap execution**: Read 2 rooms + 2 users → verify occupants → swap them (atomic, up to 6 documents)
- **Double-booking prevention**: Room `occupant_uid` is verified inside the transaction before any update

Even at low traffic, concurrent requests are handled correctly. The `version` field provides an additional application-level safeguard.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROJECT_ID` | Yes | `biu-dorm-exchange` | GCP project ID |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Local only | — | Path to service account JSON |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins |
| `MATCH_EXPIRY_HOURS` | No | `48` | Hours before a match proposal expires |
| `LISTING_EXPIRY_DAYS` | No | `30` | Days before a listing expires |

---

## GCP Free Tier Budget

| Resource | Free Tier Limit | Expected Usage | Headroom |
|----------|----------------|----------------|----------|
| Cloud Run requests | 2M/month | ~10K/month | 200x |
| Cloud Run vCPU-seconds | 360K/month | ~5K/month | 72x |
| Firestore reads | 50K/day | ~2K/day | 25x |
| Firestore writes | 20K/day | ~500/day | 40x |
| Firestore storage | 1 GiB | <10 MB | 100x |
| Firebase Auth | Unlimited | ~500 users | N/A |
| Cloud Build | 120 min/day | ~5 min/deploy | 24x |

`min-instances: 0` means zero cost when idle (cold start tradeoff acceptable for an MVP).

---

## Testing

```bash
source .venv/bin/activate

# Run all 90 tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_state_machine.py

# Run a specific test class
pytest tests/test_matching_engine.py::TestDatesOverlap

# Run a specific test
pytest tests/test_routes_listings.py::TestCreateLeaseTransfer::test_create_lease_transfer
```

Tests use mocked Firestore — no database or network access required.

---

## Interactive API Docs

When the server is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide interactive documentation where you can test endpoints directly (add your Bearer token via the Authorize button).
