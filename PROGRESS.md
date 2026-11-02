# MMUEats — Build Progress & Requirements Checklist

# MMUEats — Build Progress & Requirements Checklist

**Status: all 12 phases complete.** 136 backend tests passing, every phase
live-verified against a real running server (not just the test client), both
`npm run build` and Django's `check --deploy` clean. Full details per phase
below; honest gaps (no Flutter mobile build, no automated frontend test
suite, Docker Compose written-but-not-build-tested, a few Phase 10 "nice to
have" items deferred) are called out explicitly in their own phase sections
rather than glossed over.

This file is the source of truth for what's done, what's in progress, and what's
left across all 12 development phases. Update it at the end of every phase.

Legend: [x] done & tested · [~] partial / mocked · [ ] not started

---

## Phase 1 — Project Setup
- [x] Git repository initialized, root `.gitignore`
- [x] Backend: Django project `config` + 12 apps (authentication, users, restaurants,
      meals, orders, payments, deliveries, notifications, advertisements, promotions,
      analytics, common)
- [x] Backend: env-driven `settings.py` (SQLite dev fallback / Postgres via `DATABASE_URL`)
- [x] Backend: `.env.example` with every credential the spec requires, flagged
- [x] Backend: DRF + JWT (SimpleJWT) + drf-spectacular (Swagger/Redoc) wired
- [x] Backend: custom exception handler → consistent `{success, error:{code,message}}` envelope
- [x] Backend: custom `User` model (UUID pk, roles, `is_email_verified`, `is_approved`)
- [x] Backend: `AuditLog` model + `write_audit_log()` helper (common app)
- [x] Backend: role-based permission classes (`IsCustomer`, `IsVendor`, `IsDeliveryPartner`, `IsAdministrator`)
- [x] Backend: migrations generated & applied; superuser created; dev server verified (health check, admin, Swagger all return correct status codes)
- [x] Web: Vite + React scaffold, full dependency set installed (Router, Axios, Tailwind v4, React Icons, Framer Motion, React Hook Form, React Hot Toast, Chart.js, TanStack Query)
- [x] Web: modular `src/` structure (components, pages, layouts, hooks, services, contexts, utils, assets)
- [x] Web: MMU-inspired Tailwind theme (maroon/gold, contrast-checked)
- [x] Web: Axios client with JWT access/refresh interceptor + request queueing
- [x] Web: `AuthContext`, `ProtectedRoute` (role-aware)
- [x] Web: Navbar + Footer (footer matches spec §19 exactly incl. partner links)
- [x] Web: `npm run build` verified clean; dev server verified serving 200
- [ ] Mobile: Flutter scaffold (Phase 4 — no Flutter SDK in this sandbox; code will be written but not locally compiled/tested)
- [ ] Docker/deployment skeleton (Phase 12)

## Phase 2 — Authentication ✅ COMPLETE
- [x] Backend: `EmailVerificationToken`, `PasswordResetToken` models (one-time, expiring, invalidated on reuse/replacement)
- [x] Backend: register / login / logout / verify-email / resend-verification endpoints
- [x] Backend: forgot-password / reset-password / change-password endpoints
- [x] Backend: throttling scopes, unverified-login blocked, generic responses that don't leak account existence
- [x] Backend: email sending via Celery task (console backend in dev, real Gmail SMTP via env in prod)
- [x] Backend: 23 automated tests, all passing (registration incl. non-university email, weak/mismatched password, duplicate email; verification incl. expired/used/invalid token; resend; login gating incl. suspended accounts; `/me/`; logout blacklisting; password reset request/confirm; change-password)
- [x] Web: SignUp, Login, VerifyEmail, ResendVerification, Forgot/ResetPassword pages
- [x] Live end-to-end curl verification against running server: register → verify → login → authenticated `/me/` call, all correct
- [x] Fixed a real bug found via testing: DRF re-wraps serializer-level `ValidationError` codes through a list during `is_valid(raise_exception=True)`, silently dropping our custom error codes (e.g. `email_not_verified`) — fixed in `common/exceptions.py`

## Phase 3 — Partner Onboarding ✅ COMPLETE
- [x] `VendorApplication` / `DeliveryPartnerApplication` models with status workflow (pending/approved/rejected/needs_info)
- [x] Public submission endpoints (AllowAny) matching the web forms already built in Phase 1
- [x] Admin-only list/review endpoints (`IsAdministrator`) with approve/reject/needs-info actions
- [x] Approval creates the User account (role set, `is_approved=True`, `is_email_verified=True`, unusable password) and emails an account-setup link reusing the password-reset flow
- [x] Rejection emails the applicant with optional notes; no account created
- [x] Audit logging on every review action
- [x] 8 automated tests, all passing (submission, non-admin blocked from listing, approval creates correct user, rejection leaves no user, double-approval conflict, delivery-partner approval, unapproved-partner permission check)
- [x] Live end-to-end curl verification: public form submission → admin login → admin approval → resulting vendor account verified with correct role/flags

## Phase 4 — Customer Module ✅ COMPLETE (web)
- [x] `restaurants` app: `Restaurant`, `RestaurantImage`, `FavoriteRestaurant`, `RestaurantReview` (one review per order — DB-constraint-enforced fraud prevention)
- [x] `meals` app: `Category`, `Meal` (discount %, prep time, stock, optional nutrition), `MealImage`, `FavoriteMeal`
- [x] `orders` app: `Cart`/`CartItem` (single-restaurant enforced), `Order`/`OrderItem` (snapshotted), strict server-side status transition graph exactly matching spec §39
- [x] Cart management (add/update/remove/clear), checkout (validates availability & stock, computes totals, decrements stock, snapshots items)
- [x] Role-scoped order visibility (customer/vendor/admin), guarded status transitions, customer cancellation (only pre-preparation), reorder
- [x] Public browsing/search/filter for restaurants and meals (django-filter + SearchFilter)
- [x] 34 new automated tests, all passing (57 total project-wide): restaurant CRUD & ownership, meal CRUD & search, cart conflict/availability rules, checkout math & edge cases, full status-transition matrix, permission boundaries, reorder
- [x] Two real bugs caught and fixed via testing: Decimal/float mixing in `discounted_price`, and a DRF router URL-ordering bug where a slug catch-all route shadowed `favorites/`/`reviews/`/`mine/`
- [x] Live end-to-end curl verification: seeded data → public browse → customer login → add to cart → checkout (correct subtotal/delivery fee/total) → vendor login → accept → invalid skip-ahead correctly rejected → preparing → ready_for_pickup, all confirmed against the real running server
- [x] Web: RestaurantsPage (search), RestaurantDetailPage (menu + add-to-cart + favorite), CartPage, CheckoutPage (campus location dropdown, M-Pesa/COD choice), OrdersPage + OrderDetailPage (status tracker, cancel, reorder), FavoritesPage, `CartContext` with live navbar badge
- [ ] Vendor-side dashboard, menu management UI (Phase 5)
- [ ] Delivery-partner-side UI (Phase 6)
- [ ] M-Pesa STK push integration (Phase 7 — checkout currently supports COD fully; M-Pesa option is wired in the UI/model but the actual Daraja call comes in Phase 7)
- [ ] Mobile (Flutter) customer screens — not started; no Flutter SDK in this sandbox so this will be written but not locally compiled

## Phase 5 — Vendor Module ✅ COMPLETE
- [x] `analytics` app: `VendorDashboardView` (today's orders/revenue, pending/completed/cancelled counts, most-sold meals, ratings) and `VendorSalesReportView` (date-range revenue/order aggregation, meal performance), both `IsVendor`-gated
- [x] 4 new automated tests, all passing (65 total project-wide): dashboard 404 without a restaurant, revenue reflects delivered orders only, customer blocked from vendor dashboard, sales report aggregation
- [x] Live end-to-end curl verification against real seeded data: vendor dashboard correctly showed the Phase-4 order's meal in "most sold," sales report aggregated it correctly, vendor successfully created a new meal via the same API the frontend menu page calls
- [x] Web: `VendorLayout` (sidebar nav), `VendorDashboardPage` (stat cards + most-sold list, redirects to restaurant setup if none exists yet), `VendorRestaurantProfilePage` (create/edit storefront incl. logo/banner upload, hours, status), `VendorMenuPage` (full meal CRUD inline, availability toggle, delete with confirm), `VendorOrdersPage` (incoming orders with accept/reject/progress actions matching the exact status graph, auto-refresh polling), `VendorReportsPage` (Chart.js revenue line chart + meal performance table)
- [x] Role-based post-login redirect (vendor → `/vendor/dashboard`) and route protection (`allowedRoles={["vendor"]}`)
- [x] Production build verified clean (one benign chunk-size warning noted for future code-splitting — not urgent for current scale)

## Phase 6 — Delivery Module ✅ COMPLETE
- [x] `deliveries` app: `DeliveryPartnerProfile` (online/offline, vehicle type, earnings/rating totals), `Delivery` (pool-based assignment — auto-created when a vendor marks an order `ready_for_pickup`, sits unassigned until accepted), `DeliveryPartnerReview`
- [x] Extended `Order`'s status graph with role-gated transitions: vendors own `accepted/preparing/ready_for_pickup/rejected/cancelled`; delivery partners own `picked_up/out_for_delivery/delivered`, scoped so only the assigned partner can act (unauthorized attempts → 404, not a leaky 403)
- [x] Endpoints: partner profile, available-deliveries pool, accept/reject (race-protected — two partners can't grab the same delivery), current + history, earnings summary
- [x] 12 new tests, 74 passing project-wide. Caught and fixed a real bug: earnings/delivery-count updates relied on a profile only lazily created elsewhere — fixed with `get_or_create`. Updated 2 Phase-4 tests whose expectations were superseded by the new role-based permission check
- [x] Full live curl run of the entire journey: seeded order → drove to `ready_for_pickup` as vendor → confirmed it appeared in rider's pool → accepted → pickup → out for delivery → delivered → earnings correctly credited
- [x] Web: `DeliveryLayout`, `DeliveryDashboardPage` (online toggle + stats), `AvailableDeliveriesPage` (polling, accept), `CurrentDeliveryPage` (pickup/delivery actions, reject-before-pickup), `DeliveryHistoryPage`, `EarningsPage`. Production build verified clean. Role-based routing wired

## Phase 7 — Payments ✅ COMPLETE
- [x] `payments` app: `Payment` model created automatically at checkout for every order (uniform history across methods) — COD starts pending and auto-marks paid on delivery; M-Pesa starts pending, moves to processing on STK push, paid/failed on callback
- [x] `mpesa_service.py`: real Safaricom Daraja sandbox integration (OAuth token, STK push, password generation) — with a clean, safety-guarded **mock mode** that activates automatically whenever `MPESA_CONSUMER_KEY/SECRET/PASSKEY` aren't set, so development never blocks on waiting for credentials. Mock mode requires zero code changes to switch off — just fill in the env vars
- [x] Endpoints: STK push initiation, Safaricom webhook callback (unauthenticated, validated by payload shape, never 500s on malformed input), a dev-only simulate-callback endpoint (safe by construction — only ever acts on `is_mocked=True` payments, which can only exist without real credentials), payment history
- [x] 10 new tests, 84 passing project-wide. Caught and fixed two real bugs: a `settings.DEBUG`-based safety gate that silently broke under Django's test runner (which always forces `DEBUG=False`) — replaced with a safer `is_mocked`-based guard; and a classic form-data boolean bug (`"False"` as a string is truthy in Python) in the simulate endpoint's success/failure flag parsing
- [x] Live end-to-end curl verification: real checkout → mocked STK push (correct amount) → simulated customer completion → payment history correctly showing `paid` status and mock M-Pesa receipt number
- [x] Web: `CheckoutPage` now branches on payment method — M-Pesa collects a phone number, triggers the STK push, and shows a waiting screen with dev-mode simulate buttons when running against mock credentials; `OrderDetailPage` shows live payment status and offers a "Pay with M-Pesa" retry for any still-pending M-Pesa order
- [x] Production build verified clean
- [ ] Student Wallet (explicitly future/out-of-scope per spec §37, §84 — not implemented)

## Phase 8 — Notifications ✅ COMPLETE
- [x] `notifications` app: `Notification` (in-app record, type enum covering every spec §41 event), `DeviceToken` (FCM registration per user/platform)
- [x] `fcm_service.py`: real Firebase Cloud Messaging integration (`firebase-admin` installed) with the same safety-guarded mock mode as M-Pesa — logs instead of sending when `FIREBASE_CONFIG` isn't set
- [x] Celery tasks for notification email + push fan-out to all of a user's active devices
- [x] **Real-time layer**: Django Channels + Daphne now genuinely serve ASGI (HTTP + WebSocket) in dev — `ws/notifications/` per logged-in user, JWT-authenticated via query param, broadcasting both in-app notifications and live order status updates
- [x] Central `notify_user()` service (DB record + WebSocket broadcast + push/email) wired into: order status transitions (accepted/preparing/ready/out-for-delivery/delivered/cancelled/rejected), delivery-partner assignment, vendor/delivery-partner application approval
- [x] REST API: list/unread-count/mark-read/mark-all-read, device token registration
- [x] 10 new tests, 94 passing project-wide. Caught and fixed two real bugs: a DRF auto-generated `UniqueValidator` silently blocking the intended re-registration `update_or_create` flow for device tokens, and confirmed (via a genuine two-process test) that the in-memory channel layer only works within a single process — informed the live-verification approach below
- [x] **Live end-to-end verification with a real WebSocket client**: connected as a customer, had a vendor accept the order over a separate HTTP call to the *same* running server process, and watched the `order_update` event arrive on the socket in real time, unprompted
- [x] Web: `NotificationContext` (REST fetch + live WebSocket updates, graceful fallback if the socket can't connect), `NotificationBell` dropdown in the navbar with unread badge, `OrderDetailPage` now updates instantly via WebSocket (polling kept as a fallback belt-and-suspenders)
- [x] Production build verified clean

## Phase 9 — Advertising ✅ COMPLETE
- [x] `advertisements` app: `Advertisement` (scheduled date range, placement enum, priority, active flag), `AdvertisementImpression`/`AdvertisementClick` (anonymous-safe — tracked only by an opaque client-generated `device_id`, never IP/user-agent)
- [x] Admin CRUD, public `/active/` endpoint (only currently-valid ads for a placement, priority-ordered), impression/click tracking, per-ad CTR analytics
- [x] 13 tests, 107 passing project-wide. **Caught and fixed a real, non-obvious bug via manual curl testing**: DRF's `BooleanField` treats a missing key in multipart form data using HTML-checkbox semantics ("absent = unchecked = False"), which silently overrode the model's `default=True` for `is_active` on any multipart create that omitted the field — fixed with a custom `ExplicitBooleanField` restoring normal REST semantics (missing = use default), with a regression test locking in the correct behavior
- [x] Live end-to-end curl verification: admin creates ad → correctly defaults to active → appears in public `/active/` feed → anonymous impression + click tracked → admin analytics shows correct 100% CTR
- [x] Web: `StartupAdPopup` implementing the exact once-per-day flow from spec §43 (localStorage date-stamp check, impression tracking on show, click tracking + external URL open, reappears only on the next calendar day), mounted app-wide; `AdminAdvertisementsPage` (full CRUD with image upload, date range, priority, active toggle, live CTR stats) behind a new `AdminLayout`
- [x] Production build verified clean
- Note: the broader Admin Dashboard (Users/Vendors/Orders overview, promotions, full reporting) landed in Phase 10, below

## Phase 10 — Advanced Features ✅ MOSTLY COMPLETE
- [x] **Promotions/Coupons**: `Coupon`/`CouponRedemption` models (percentage/fixed/free-delivery types, min-order thresholds, per-customer usage caps, restaurant-scoping), wired into real checkout pricing (replacing the Phase 4 placeholder `discount_amount = 0`), admin CRUD, a standalone validate-without-redeeming preview endpoint. 13 tests passing
- [x] **Admin Dashboard**: platform-wide stats (users/vendors/delivery partners, order counts by status, daily/weekly/monthly/total revenue, popular meals/restaurants, pending applications), user management (list/filter by role, suspend/reactivate — confirmed a suspended user genuinely can't log in), audit log visibility (the `AuditLog` model has existed since Phase 1 but never had a read endpoint until now). 12 tests passing
- [x] 128 tests passing project-wide. **Two real "class-merge" bugs caught and fixed via careful `grep`/test verification**: a `str_replace` edit that accidentally deleted a class header line while keeping its body (once in `analytics/views.py` merging `VendorDashboardView` into `AuditLogListView`, once in `analytics/tests.py` merging `VendorDashboardTests` into `AuditLogTests`) — both caught before committing, not after
- [x] Live curl verification: admin dashboard reflects real seeded orders/revenue correctly; user listing/filtering works
- [x] Web: `AdminDashboardPage` (stat cards + popular meals/restaurants), `AdminUsersPage` (list/filter/suspend/reactivate), `AdminApplicationsPage` (vendor/delivery-partner approval UI — closing a gap where Phase 3's approval flow only ever had an API, never a UI), expanded `AdminLayout` nav, coupon code field added to `CheckoutPage`
- [x] Production build verified clean
- [ ] Recommendations (frequently-ordered/trending meals) — deferred, lower priority than the above
- [ ] Live delivery tracking on a map (Google Maps) — deferred alongside Phase 4/6 mobile work, since it's primarily a mobile/maps-SDK feature
- [ ] A dedicated admin Reports page (date-range platform-wide reporting UI) — the backend data exists via the dashboard endpoint; a richer filterable UI can be added on request

## Phase 11 — Testing ✅ BACKEND COMPLETE / FRONTEND MANUAL ONLY
- [x] **136 automated backend tests, all passing** — unit + integration across every app: authentication (23), partner onboarding (8), restaurants (6), meals (6), orders (14), analytics/vendor (4), deliveries (12), payments (10), notifications (10), advertisements (13), promotions (13), analytics/admin (12), plus a new cross-app pass this phase (8 tests: favorites CRUD, saved delivery locations, vendor order rejection, and one comprehensive integration test driving a single order through coupon pricing → M-Pesa mock payment → vendor acceptance → delivery-partner pool assignment/handoff → notifications firing at each step → both review types → final order/payment history — every phase's machinery working together in one continuous scenario, passing on the first run)
- [x] Every phase was also live-verified against a real running server via curl (not just Django's test client) at the time it was built — registration/verification/login, partner approval, the full order lifecycle, M-Pesa mock flow, real-time WebSocket delivery, advertisement tracking, admin dashboard — so this phase's 136-test suite is a regression net on top of work that was already proven live, not the first time any of it has run
- [x] Real bugs were caught throughout by this testing discipline (documented in each phase's notes above): Decimal/float mixing, a DRF router URL-ordering conflict, a DRF error-code-dropping quirk, a lazily-created-profile earnings bug, a `DEBUG`-incompatible safety gate, a classic stringly-typed boolean bug, a DRF multipart-form `BooleanField` HTML-checkbox quirk, and two self-inflicted "class-merge" editing mistakes — all caught and fixed before commit, several with regression tests added specifically to lock in the fix
- [ ] **No automated frontend test suite** (Vitest/React Testing Library/Cypress) was set up — frontend correctness was verified via production builds (clean at every phase) and manual/live interaction with the real backend, not automated JS tests. This is the most honest gap to flag: the backend has real regression coverage, the frontend does not yet
- [ ] Formal UI/E2E testing (spec §66's "UI Testing", "End-to-End Testing" rows) is therefore not implemented — would require adding a JS test runner and writing component/flow tests, which hasn't been done given the scope already covered

## Phase 12 — Deployment ✅ COMPLETE (written & validated; not build-tested — no Docker in this sandbox)
- [x] `backend/Dockerfile`: Python 3.12-slim, builds psycopg2 from source, collects static files at build time (safe — no real env vars needed for that step), Daphne serves both HTTP and WebSocket over one ASGI app on port 8000, includes a `HEALTHCHECK` against `/api/health/`
- [x] `backend/docker-entrypoint.sh`: waits for Postgres to accept connections (polls with `psycopg2`, 30 retries), runs migrations, then execs whatever command the service was given — shared by both the `backend` and `celery_worker` services so migrations are never missed regardless of which container starts first. Shell syntax and the embedded Python were both validated (`sh -n`, `py_compile`) since Docker itself isn't available to test a real build
- [x] `web/Dockerfile`: multi-stage — Node 20 builds the Vite production bundle (relative `/api` base URL by default, so the deployed frontend and API share one origin and never need CORS), then an Nginx Alpine stage serves it
- [x] `web/nginx.conf`: serves the React SPA (with client-side routing fallback), reverse-proxies `/api/`, `/admin/`, and `/ws/` (with the `Upgrade`/`Connection` headers and long read/send timeouts a WebSocket needs) to the backend, serves `/static/` and `/media/` from shared Docker volumes
- [x] `docker-compose.yml`: Postgres 16, Redis 7, the Daphne backend, an independently-scalable Celery worker, and the Nginx+React web service, wired with health-check-gated `depends_on` so nothing starts before its dependencies are actually ready. Syntax-validated with PyYAML (`yaml.safe_load`) since the `docker` CLI isn't available in this sandbox
- [x] **Production security hardening**: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS (with subdomains + preload), `SECURE_CONTENT_TYPE_NOSNIFF`, and `SECURE_PROXY_SSL_HEADER` — all gated behind `if not DEBUG` so local dev is never affected. Verified with Django's own `manage.py check --deploy` under `DEBUG=False`: **zero security warnings** (the 55 issues that command reports are 100% cosmetic drf-spectacular Swagger-doc warnings from using plain `APIView` instead of `GenericAPIView`, unrelated to security)
- [x] **A real production bug caught and fixed before it could bite**: the frontend's WebSocket URL builder assumed `VITE_API_BASE_URL` was always an absolute `http://...` URL and did a string transform on it — which silently breaks in production, where the URL is relative (`/api`) since the frontend and API share an origin behind Nginx. Fixed to derive the WebSocket origin from `window.location` whenever the API base is relative, with dev-mode behavior unchanged
- [x] Root `README.md` with full local-dev and Docker deployment instructions (spec §67's Installation/Deployment Guide), a `.env.docker.example` documenting the Compose-level config separately from `backend/.env`'s application-level config, and notes on scaling (object storage swap-in, independently scalable Celery workers) for a real production rollout
- [x] Full test suite (136 tests) and both `npm run build` (backend/web) re-verified clean immediately before this commit
- **Honest limitation**: `docker compose up --build` itself was never executed, because this sandbox has no Docker daemon. Every file was written carefully and validated at the syntax/logic level available without Docker (shell syntax, embedded Python compilation, YAML parsing, Django's deploy checklist) — but an actual end-to-end container build/boot has not happened. Please run it for real before a production launch and report back if anything doesn't come up cleanly.

---

## Environment variables still needed from you (nothing else is blocking development)
| Variable | Needed for | Status |
|---|---|---|
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | Real Gmail SMTP sending | Using console backend (prints emails to log) until provided |
| `MPESA_CONSUMER_KEY/SECRET/PASSKEY/SHORTCODE` | M-Pesa Daraja payments | Will build against Safaricom sandbox defaults until provided |
| `FIREBASE_CONFIG` | Push notifications | Will mock/no-op until provided |
| `GOOGLE_MAPS_API_KEY` | Delivery navigation/maps | Will stub map components until provided |
| Postgres `DATABASE_URL` | Production database | SQLite used for dev; no action needed until deployment |


## Follow-up: Customer dashboard
- Replaced `DashboardPlaceholder` with `web/src/pages/CustomerDashboardPage.jsx` (stats, active orders, top-rated restaurants, popular meals, reorder, favorites, notifications).

## Follow-up: Search, avatar cropper, vendors home, banner, categories, meal detail, quantities, reviews, favorites
- Navbar search (live menu suggestions), bell/cart aligned; avatar upload (crop 1:1, preview, save, delete); upload bug fixed
  (axios sent FormData as JSON); password change blacklists sessions + forces re-login.
- Customers land on /restaurants after login: 3-slide auto-rotating banner (3000ms, swipe, dots), category chips, meal cards,
  meal detail page, quantity steppers, cart images; meal + vendor ratings/reviews/favorites.
- Backend: MealReview, Meal.ratings_count, favorite_id on lists, Advertisement.description/cta_label + internal links, avatar delete endpoint.
