# Frontend Implementation Plan — BIU Dormitory Exchange Platform

## Overview

React + Vite + Tailwind CSS frontend in a `frontend/` directory alongside the existing FastAPI backend. Uses Firebase Auth JS SDK for login/signup, Axios for API calls with automatic token injection, and TanStack React Query for server state. Deploys to Firebase Hosting (free tier).

---

## Directory Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── firebase.json              # Firebase Hosting config
├── .firebaserc                 # Firebase project alias
├── .env.example
├── public/
│   └── favicon.ico
└── src/
    ├── main.tsx                # ReactDOM.createRoot + providers
    ├── App.tsx                 # Router + layout
    ├── firebase.ts             # Firebase app init + auth instance
    ├── api/
    │   └── client.ts           # Axios instance with auth interceptor
    ├── hooks/
    │   ├── useAuth.ts          # AuthContext: login, signup, logout, currentUser, loading
    │   ├── useListings.ts      # useListings, useMyListings, useListing, useCreateListing, useCancelListing, useClaimListing
    │   ├── useMatches.ts       # useMyMatches, useMatch, useAcceptMatch, useRejectMatch
    │   ├── useTransactions.ts  # useMyTransactions, useTransaction, useConfirmTx, useCancelTx
    │   ├── useRooms.ts         # useRooms, useRoom
    │   └── useProfile.ts      # useProfile, useCreateProfile, useUpdateProfile
    ├── components/
    │   ├── Layout.tsx          # Shell: sidebar/topbar + <Outlet/>
    │   ├── ProtectedRoute.tsx  # Redirect to /login if not authed
    │   ├── StatusBadge.tsx     # Colored pill for listing/match/tx status
    │   ├── ListingCard.tsx     # Card for browse grid
    │   ├── RoomBadge.tsx       # Category A/B/C colored badge
    │   ├── EmptyState.tsx      # Empty list placeholder
    │   └── LoadingSpinner.tsx  # Centered spinner
    ├── pages/
    │   ├── LoginPage.tsx       # Email/password login + signup toggle
    │   ├── OnboardingPage.tsx  # Create profile (name, student ID, phone)
    │   ├── DashboardPage.tsx   # Summary cards: my listings, pending matches, active txns
    │   ├── BrowseListingsPage.tsx   # Filter bar + paginated listing grid
    │   ├── ListingDetailPage.tsx    # Full listing info + claim button
    │   ├── CreateListingPage.tsx    # Tabbed form: lease transfer | swap request
    │   ├── MyListingsPage.tsx       # User's own listings with status
    │   ├── MatchesPage.tsx          # Incoming/outgoing matches, accept/reject
    │   ├── TransactionsPage.tsx     # Active transactions, confirm/cancel
    │   └── CompatibleSwapsPage.tsx  # Compatible swap results for a listing
    └── types/
        └── index.ts            # TypeScript interfaces mirroring backend models
```

---

## Key Files and Their Responsibilities

### `src/firebase.ts`
- Initialize Firebase app with config from env vars (`VITE_FIREBASE_*`)
- Export `auth` instance from `firebase/auth`

### `src/api/client.ts`
- Create Axios instance with `baseURL` from `VITE_API_URL` (default `http://localhost:8000`)
- Request interceptor: get current user's ID token via `auth.currentUser.getIdToken()`, attach as `Authorization: Bearer <token>`
- Response interceptor: normalize error shapes

### `src/hooks/useAuth.ts`
- React Context wrapping `onAuthStateChanged`
- Provides: `user`, `loading`, `signIn(email, password)`, `signUp(email, password)`, `signOut()`
- On first auth, check if profile exists (`GET /api/v1/users/me`) — if 404, redirect to `/onboarding`

### `src/hooks/useListings.ts` (TanStack React Query)
- `useListings(filters)` → `GET /api/v1/listings` with query params (type, category, status, building, page, limit)
- `useMyListings(status?)` → `GET /api/v1/listings/my`
- `useListing(id)` → `GET /api/v1/listings/{id}`
- `useCreateLeaseTransfer()` → `POST /api/v1/listings/lease-transfer` (mutation)
- `useCreateSwapRequest()` → `POST /api/v1/listings/swap-request` (mutation)
- `useUpdateListing()` → `PUT /api/v1/listings/{id}` (mutation)
- `useCancelListing()` → `POST /api/v1/listings/{id}/cancel` (mutation)
- `useClaimListing()` → `POST /api/v1/listings/{id}/claim` (mutation)
- `useCompatibleSwaps(id)` → `GET /api/v1/listings/{id}/compatible`

### `src/hooks/useMatches.ts`
- `useMyMatches(status?)` → `GET /api/v1/matches/my`
- `useMatch(id)` → `GET /api/v1/matches/{id}`
- `useAcceptMatch()` → `POST /api/v1/matches/{id}/accept` (mutation)
- `useRejectMatch()` → `POST /api/v1/matches/{id}/reject` (mutation)

### `src/hooks/useTransactions.ts`
- `useMyTransactions(status?)` → `GET /api/v1/transactions/my`
- `useTransaction(id)` → `GET /api/v1/transactions/{id}`
- `useConfirmTransaction()` → `POST /api/v1/transactions/{id}/confirm` (mutation)
- `useCancelTransaction()` → `POST /api/v1/transactions/{id}/cancel` (mutation)

### `src/types/index.ts`
TypeScript interfaces matching backend response models:
- `UserProfile`, `UserProfilePublic`, `UserProfileCreate`, `UserProfileUpdate`
- `Room`, `RoomCreate`
- `ListingResponse`, `PaginatedListings`, `LeaseTransferCreate`, `SwapRequestCreate`, `ListingUpdate`, `ClaimRequest`
- `MatchResponse`
- `TransactionResponse`
- Enums: `RoomCategory`, `ListingType`, `LeaseTransferStatus`, `SwapRequestStatus`, `MatchStatus`, `TransactionStatus`

---

## Routing

```
/login              → LoginPage (public)
/onboarding         → OnboardingPage (authed, no profile yet)
/                   → DashboardPage (authed)
/listings           → BrowseListingsPage (authed)
/listings/new       → CreateListingPage (authed)
/listings/:id       → ListingDetailPage (authed)
/listings/:id/compatible → CompatibleSwapsPage (authed)
/my-listings        → MyListingsPage (authed)
/matches            → MatchesPage (authed)
/transactions       → TransactionsPage (authed)
```

All authed routes wrapped in `<ProtectedRoute>` which checks `useAuth()` and redirects to `/login`.

---

## Page Details

### LoginPage
- Email + password form
- Toggle between "Sign In" and "Sign Up" mode
- Uses Firebase Auth `signInWithEmailAndPassword` / `createUserWithEmailAndPassword`
- On success: check profile → redirect to `/` or `/onboarding`

### OnboardingPage
- Form: full_name, student_id, phone
- Calls `POST /api/v1/users/profile`
- On success: redirect to `/`

### DashboardPage
- Three summary cards:
  - My active listings (count + link to /my-listings)
  - Pending matches requiring action (count + link to /matches)
  - Active transactions (count + link to /transactions)
- Quick action button: "Create New Listing"

### BrowseListingsPage
- Filter bar: listing type (dropdown), room category (checkboxes A/B/C), building (text input), date range
- Paginated grid of `<ListingCard>` components
- Each card shows: room info, category badge, lease dates, listing type, asking price (if lease transfer)
- Click → navigates to `/listings/:id`

### ListingDetailPage
- Full listing details
- If lease transfer from another user: "Claim This Room" button
- If swap request from another user: "Offer Swap" button (submits with `claimant_listing_id`)
- If own listing: edit/cancel buttons
- Shows match status if matched

### CreateListingPage
- Two tabs: "Lease Transfer" | "Swap Request"
- Lease Transfer form: room selection, lease dates, description, asking price
- Swap Request form: room selection, lease dates, description, desired categories (multi-select), desired buildings
- Room selection: dropdown populated from `GET /api/v1/rooms` (filtered to user's room)

### MyListingsPage
- List of user's listings with status badges
- Actions per listing based on status: Edit (OPEN), Cancel (OPEN/MATCHED), View matches

### MatchesPage
- Two sections: "Incoming" (matches on my listings) and "Outgoing" (matches I created)
- Each match shows: room offered, category, building, status
- Action buttons: Accept / Reject (for PROPOSED matches on my listings)

### TransactionsPage
- List of active/recent transactions
- Shows: type, parties, room(s), status
- Actions: Confirm (PENDING) / Cancel

### CompatibleSwapsPage
- Reached from ListingDetailPage for swap requests
- Shows compatible swap partners from `GET /api/v1/listings/{id}/compatible`
- "Offer Swap" button on each compatible listing

---

## Implementation Phases

### Phase 1: Project Setup
- `npm create vite@latest frontend -- --template react-ts`
- Install deps: `tailwindcss`, `postcss`, `autoprefixer`, `react-router-dom`, `@tanstack/react-query`, `axios`, `firebase`
- Configure Tailwind, PostCSS, Vite proxy (dev server proxies `/api` to `localhost:8000`)
- Create `.env.example` with `VITE_API_URL` and `VITE_FIREBASE_*` vars
- **Files**: `package.json`, `vite.config.ts`, `tailwind.config.js`, `postcss.config.js`, `.env.example`, `src/main.tsx`
- **Commit**: `feat(frontend): project scaffold with Vite, React, Tailwind, and dependencies`

### Phase 2: Firebase Auth + API Client
- `src/firebase.ts` — Firebase init
- `src/api/client.ts` — Axios with token interceptor
- `src/hooks/useAuth.ts` — AuthContext with onAuthStateChanged
- `src/types/index.ts` — All TypeScript interfaces and enums
- **Commit**: `feat(frontend): Firebase auth context, Axios API client, and TypeScript types`

### Phase 3: App Shell + Routing
- `src/App.tsx` — React Router with all routes
- `src/components/Layout.tsx` — Sidebar navigation + top bar with user info + logout
- `src/components/ProtectedRoute.tsx` — Auth guard
- `src/components/LoadingSpinner.tsx`, `EmptyState.tsx`, `StatusBadge.tsx`, `RoomBadge.tsx`
- `src/pages/LoginPage.tsx` — Login/signup form
- `src/pages/OnboardingPage.tsx` — Profile creation form
- **Commit**: `feat(frontend): app shell with routing, layout, login, and onboarding pages`

### Phase 4: Dashboard + Profile Hooks
- `src/hooks/useProfile.ts`
- `src/pages/DashboardPage.tsx` — Summary cards with counts
- **Commit**: `feat(frontend): dashboard page with summary cards and profile hooks`

### Phase 5: Listings (Browse + Create + Detail)
- `src/hooks/useListings.ts` — All listing queries and mutations
- `src/hooks/useRooms.ts` — Room queries for form dropdowns
- `src/components/ListingCard.tsx`
- `src/pages/BrowseListingsPage.tsx` — Filter bar + paginated grid
- `src/pages/CreateListingPage.tsx` — Tabbed creation form
- `src/pages/ListingDetailPage.tsx` — Detail view with claim/edit actions
- `src/pages/MyListingsPage.tsx` — User's listings
- `src/pages/CompatibleSwapsPage.tsx` — Compatible swap results
- **Commit**: `feat(frontend): listing pages with browse, create, detail, and compatible swaps`

### Phase 6: Matches + Transactions
- `src/hooks/useMatches.ts`
- `src/hooks/useTransactions.ts`
- `src/pages/MatchesPage.tsx` — Accept/reject interface
- `src/pages/TransactionsPage.tsx` — Confirm/cancel interface
- **Commit**: `feat(frontend): matches and transactions pages with accept/reject/confirm flows`

### Phase 7: Polish + Firebase Hosting Config
- Responsive design pass (mobile-friendly)
- Error toast notifications for failed mutations
- `firebase.json` — Hosting config with SPA rewrite
- `.firebaserc` — Project alias
- Update root `README.md` with frontend dev/deploy instructions
- **Commit**: `feat(frontend): responsive polish and Firebase Hosting configuration`

---

## Firebase Hosting Deployment

```bash
cd frontend
npm run build
firebase login
firebase init hosting  # select dist/ as public dir, configure as SPA
firebase deploy --only hosting
```

`firebase.json`:
```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
```

---

## Environment Variables

| Variable | Dev Default | Production |
|----------|-----------|------------|
| `VITE_API_URL` | `http://localhost:8000` | Cloud Run URL |
| `VITE_FIREBASE_API_KEY` | from Firebase console | same |
| `VITE_FIREBASE_AUTH_DOMAIN` | `biu-dorm-exchange.firebaseapp.com` | same |
| `VITE_FIREBASE_PROJECT_ID` | `biu-dorm-exchange` | same |

---

## Verification

After each phase:
1. `cd frontend && npm run dev` — dev server starts
2. Navigate to `http://localhost:5173` — pages render
3. After Phase 2: login/signup works with Firebase Auth
4. After Phase 5: can browse and create listings (requires backend running)
5. After Phase 7: `npm run build` succeeds, `firebase deploy` works

---

## Key Design Decisions

- **Vite proxy in dev**: `vite.config.ts` proxies `/api` to `localhost:8000` so no CORS issues during development
- **Token refresh**: Axios interceptor calls `getIdToken(true)` to force refresh if token is about to expire
- **Optimistic updates**: TanStack React Query `onMutate` for cancel/accept/reject for snappy UX
- **No global state library**: Auth context + React Query covers all state needs
- **TypeScript strict mode**: All API responses typed, no `any`
Show less
Let me start implementing the frontend. I'll work through all 7 phases.

Update Todos

Phase 1: Project scaffold with Vite, React, Tailwind

Phase 2: Firebase Auth + API client + TypeScript types

Phase 3: App shell, routing, login, onboarding

Phase 4: Dashboard + profile hooks

Phase 5: Listings pages (browse, create, detail)

Phase 6: Matches + Transactions pages

Phase 7: Polish + Firebase Hosting config
Bash Create Vite React TypeScript project
IN
cd "/Users/kidus/Desktop/Flat-Matching-for-Dormitories." && npm create vite@latest frontend -- --template react-ts 2>&1

OUT
npm warn exec The following package was not found and will be installed: create-vite@8.2.0

> npx
> "create-vite" frontend --template react-ts

│
◇  Scaffolding project in /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend...
│
└  Done. Now run:

  cd frontend
  npm install
  npm run dev
Bash Install all frontend dependencies
IN
cd "/Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend" && npm install && npm install react-router-dom @tanstack/react-query axios firebase tailwindcss @tailwindcss/vite 2>&1

OUT
added 175 packages, and audited 176 packages in 21s

45 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities

added 123 packages, and audited 299 packages in 19s

59 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
Now let me set up the project structure and configuration files. I'll create multiple files in parallel.

Read vite.config.ts
Read main.tsx
Read index.html
Read tsconfig.json
Write vite.config.ts
16 lines
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
Write index.html
13 lines
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BIU Dorm Exchange</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
Write index.css
Write failed
@import "tailwindcss";
Write .env.example
Write failed
VITE_API_URL=https://biu-dorm-exchange-757030388279.us-central1.run.app
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=barilan-exchange.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=barilan-exchange
Read index.css
Write index.css
2 lines
@import "tailwindcss";
Write .env.example
5 lines
VITE_API_URL=https://biu-dorm-exchange-757030388279.us-central1.run.app
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=barilan-exchange.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=barilan-exchange
Now let me create the directory structure and all the source files. I'll do Phases 1-3 together since they're foundational, then tackle the remaining phases.

Bash Create source directory structure
IN
cd "/Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src" && mkdir -p api hooks components pages types && rm -f App.css App.tsx

OUT
0
Now let me create all the core files. I'll launch parallel agents for the different layers.

Task:Create frontend types and firebase
IN
Create the following files for the BIU Dormitory Exchange frontend React app. Write the files using the Write tool.

The backend API is at https://biu-dorm-exchange-757030388279.us-central1.run.app with these response models:

Backend models (from Pydantic):
- UserProfile: uid, email, full_name, student_id, phone, current_room_id?, created_at?, updated_at?
- UserProfilePublic: uid, full_name, current_room_id?
- UserProfileCreate: full_name, student_id, phone, current_room_id?
- UserProfileUpdate: full_name?, phone?, current_room_id?
- Room: id, building, floor, room_number, category(A|B|C), description, amenities[], occupant_uid?, is_active, created_at?, updated_at?
- RoomCreate: building, floor, room_number, category, description?, amenities?
- RoomUpdate: description?, amenities?, is_active?
- LeaseTransferCreate: room_id, lease_start_date, lease_end_date, description?, asking_price?
- SwapRequestCreate: room_id, lease_start_date, lease_end_date, description?, desired_categories[], desired_buildings?, desired_min_start?, desired_max_end?
- ListingUpdate: description?, asking_price?, lease_start_date?, lease_end_date?, desired_categories?, desired_buildings?
- ClaimRequest: message?, claimant_listing_id?
- ListingResponse: id, listing_type, status, owner_uid, room_id, room_category, room_building, lease_start_date, lease_end_date, description, asking_price?, desired_categories?, desired_buildings?, desired_min_start?, desired_max_end?, replacement_match_id?, target_match_id?, expires_at?, created_at?, updated_at?
- PaginatedListings: items[], total, page, limit, has_next
- MatchResponse: id, match_type, status, listing_id, claimant_uid, claimant_listing_id?, offered_room_id, offered_room_category, offered_room_building, proposed_at?, responded_at?, expires_at?, created_at?, updated_at?
- TransactionResponse: id, transaction_type, status, match_id?, match_ids?, from_uid?, to_uid?, room_id?, party_a_uid?, party_a_room_id?, party_b_uid?, party_b_room_id?, lease_start_date?, lease_end_date?, initiated_at?, completed_at?, created_at?, updated_at?

Enums:
- RoomCategory: A, B, C
- ListingType: LEASE_TRANSFER, SWAP_REQUEST
- LeaseTransferStatus: OPEN, MATCHED, PENDING_APPROVAL, COMPLETED, CANCELLED, EXPIRED
- SwapRequestStatus: OPEN, PARTIAL_MATCH, FULLY_MATCHED, PENDING_APPROVAL, COMPLETED, CANCELLED, EXPIRED
- MatchStatus: PROPOSED, ACCEPTED, REJECTED, EXPIRED, CANCELLED
- TransactionStatus: PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED

**File 1: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/types/index.ts**
- TypeScript interfaces and enums matching all backend models above
- Use string enums
- dates as string (ISO format from API)

**File 2: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/firebase.ts**
- Initialize Firebase app from VITE_ env vars
- Export `auth` from firebase/auth
- Use getAuth()

**File 3: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/api/client.ts**
- Axios instance
- baseURL from `import.meta.env.VITE_API_URL` or empty string (for proxy)
- Request interceptor: if firebase auth currentUser exists, get ID token and attach as Bearer
- Export the axios instance as default
Task:Create frontend hooks
IN
Create the following React hook files for the BIU Dormitory Exchange frontend. Write them using the Write tool.

All hooks use TanStack React Query (@tanstack/react-query). Import the api client from `../api/client` (default export, an axios instance). Import types from `../types`.

API base paths:
- Users: /api/v1/users
- Rooms: /api/v1/rooms
- Listings: /api/v1/listings
- Matches: /api/v1/matches
- Transactions: /api/v1/transactions

**File 1: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/hooks/useAuth.ts**
- AuthContext with React Context
- State: user (Firebase User | null), loading (boolean), hasProfile (boolean | null)
- Uses onAuthStateChanged from firebase/auth
- When user authenticates, check if profile exists by calling GET /api/v1/users/me — set hasProfile=true on 200, false on 404
- Exports: AuthProvider component, useAuth hook
- signIn(email, password) using signInWithEmailAndPassword
- signUp(email, password) using createUserWithEmailAndPassword
- logOut() using signOut
- Import auth from `../firebase`

**File 2: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/hooks/useProfile.ts**
- useProfile(): useQuery for GET /api/v1/users/me, returns UserProfile
- useCreateProfile(): useMutation for POST /api/v1/users/profile, body is UserProfileCreate
- useUpdateProfile(): useMutation for PUT /api/v1/users/me, body is UserProfileUpdate
- Invalidate ['profile'] on mutations

**File 3: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/hooks/useRooms.ts**
- useRooms(category?, building?): useQuery for GET /api/v1/rooms with query params
- useRoom(roomId): useQuery for GET /api/v1/rooms/{roomId}

**File 4: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/hooks/useListings.ts**
- useListings(filters): useQuery for GET /api/v1/listings with params (type, category, status, building, page, limit). Returns PaginatedListings
- useMyListings(status?): useQuery for GET /api/v1/listings/my
- useListing(id): useQuery for GET /api/v1/listings/{id}
- useCreateLeaseTransfer(): useMutation POST /api/v1/listings/lease-transfer
- useCreateSwapRequest(): useMutation POST /api/v1/listings/swap-request
- useUpdateListing(): useMutation PUT /api/v1/listings/{id}
- useCancelListing(): useMutation POST /api/v1/listings/{id}/cancel
- useClaimListing(): useMutation POST /api/v1/listings/{id}/claim, body is ClaimRequest
- useCompatibleSwaps(id): useQuery GET /api/v1/listings/{id}/compatible
- Invalidate ['listings'] on mutations

**File 5: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/hooks/useMatches.ts**
- useMyMatches(status?): useQuery GET /api/v1/matches/my
- useMatch(id): useQuery GET /api/v1/matches/{id}
- useAcceptMatch(): useMutation POST /api/v1/matches/{id}/accept
- useRejectMatch(): useMutation POST /api/v1/matches/{id}/reject
- Invalidate ['matches'] and ['listings'] on mutations

**File 6: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/hooks/useTransactions.ts**
- useMyTransactions(status?): useQuery GET /api/v1/transactions/my
- useTransaction(id): useQuery GET /api/v1/transactions/{id}
- useConfirmTransaction(): useMutation POST /api/v1/transactions/{id}/confirm
- useCancelTransaction(): useMutation POST /api/v1/transactions/{id}/cancel
- Invalidate ['transactions'] and ['matches'] and ['listings'] on mutations

Types to import from ../types:
UserProfile, UserProfileCreate, UserProfileUpdate, Room, ListingResponse, PaginatedListings, LeaseTransferCreate, SwapRequestCreate, ListingUpdate, ClaimRequest, MatchResponse, TransactionResponse
Task:Create frontend components
IN
Create the following React component files for the BIU Dormitory Exchange frontend. Use Tailwind CSS v4 classes (utility classes). Write them using the Write tool.

**File 1: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/LoadingSpinner.tsx**
- Centered spinner using a spinning border div
- Tailwind: flex items-center justify-center, animate-spin, border, rounded-full
- Takes optional className prop

**File 2: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/EmptyState.tsx**
- Props: message (string), actionLabel? (string), onAction? () => void
- Centered text with optional button
- Gray text, if actionLabel provided show a blue button

**File 3: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/StatusBadge.tsx**
- Props: status (string)
- Colored pill/badge based on status:
  - OPEN/PROPOSED/PENDING -> yellow bg
  - MATCHED/PARTIAL_MATCH/FULLY_MATCHED/ACCEPTED/IN_PROGRESS -> blue bg
  - COMPLETED -> green bg
  - CANCELLED/REJECTED/FAILED/EXPIRED -> red bg
- Use rounded-full px-2 py-0.5 text-xs font-medium

**File 4: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/RoomBadge.tsx**
- Props: category (string - "A" | "B" | "C")
- Colored badge:
  - A -> green (bg-green-100 text-green-800)
  - B -> blue (bg-blue-100 text-blue-800)
  - C -> orange (bg-orange-100 text-orange-800)
- Shows "Cat A", "Cat B", "Cat C"

**File 5: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/ListingCard.tsx**
- Props: listing (ListingResponse), onClick () => void
- Card with border, rounded, shadow-sm, hover:shadow-md, cursor-pointer, p-4
- Shows: room_building + room info, RoomBadge for category, StatusBadge for status
- Shows listing_type as "Lease Transfer" or "Swap Request"
- Shows lease dates formatted
- If asking_price, show price in ILS
- Import types from ../types, StatusBadge and RoomBadge from same dir

**File 6: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/ProtectedRoute.tsx**
- Uses useAuth from ../hooks/useAuth
- If loading, show LoadingSpinner
- If no user, Navigate to /login
- If user but hasProfile === false, Navigate to /onboarding (unless current path IS /onboarding)
- Otherwise render Outlet

**File 7: /Users/kidus/Desktop/Flat-Matching-for-Dormitories./frontend/src/components/Layout.tsx**
- App shell with sidebar + main content area
- Sidebar: fixed left, w-64, bg-gray-900 text-white, full height
- Logo/title at top: "BIU Dorm Exchange"
- Nav links: Dashboard (/), Browse Listings (/listings), Create Listing (/listings/new), My Listings (/my-listings), Matches (/matches), Transactions (/transactions)
- Use NavLink from react-router-dom for active state styling
- Top bar in main area: shows user email from useAuth, logout button
- Main content: Outlet from react-router-dom
- Mobile responsive: hamburger toggle for sidebar on small screens (use useState for open/close)
You've hit your limit · resets 3am (Asia/Jerusalem)