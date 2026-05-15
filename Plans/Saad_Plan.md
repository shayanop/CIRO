# 📱 Saad – Mobile Dev: Flutter App & UX
## Individual 5-Day Plan

> **Role**: Build the entire Flutter mobile application (mandatory deliverable), implement all screens, connect to backend REST API, and own end-to-end scenario testing.

---

## Day 1 – Flutter App Initialisation

### Pre-Meeting (All Members)
- [ ] Join stand-up call on Google Meet
- [ ] Clone the monorepo and create feature branch: `git checkout -b feat/saad-day1`

### Flutter Project Setup
- [ ] `flutter create ciro_app --org com.ciro --platforms android,ios`
- [ ] `cd ciro_app && code .` – open in VS Code
- [ ] Edit `pubspec.yaml` – add dependencies:
  ```yaml
  dependencies:
    flutter:
      sdk: flutter
    http: ^1.2.0
    provider: ^6.1.2
    google_maps_flutter: ^2.5.3
    lottie: ^3.1.0
    intl: ^0.19.0
    shared_preferences: ^2.2.2
    flutter_spinkit: ^5.2.0
  ```
- [ ] `flutter pub get` – resolve all dependencies

### Folder Structure
- [ ] Create screen files:
  - `lib/screens/home_screen.dart` – dashboard with before/after
  - `lib/screens/crisis_feed_screen.dart` – list of detected crises
  - `lib/screens/map_screen.dart` – Google Maps with overlays
  - `lib/screens/alerts_screen.dart` – dispatched alerts and tickets
  - `lib/screens/trace_screen.dart` – agent trace stepper
- [ ] Create `lib/models/` – Dart equivalents of Pydantic models
- [ ] Create `lib/services/api_service.dart` – HTTP client (base URL: `http://10.0.2.2:8000`)
- [ ] Create `lib/providers/ciro_provider.dart` – ChangeNotifier state management

### Main App Setup
- [ ] Set up `MaterialApp` in `main.dart`:
  - Define theme (`primaryColor: Color(0xFF1A3C5E)`)
  - Add `ChangeNotifierProvider`
  - Set up `BottomNavigationBar` with 5 tabs
- [ ] Run `flutter run` – confirm app launches on emulator showing 5 navigation tabs
- [ ] Add Google Maps API key to `AndroidManifest.xml`:
  ```xml
  <meta-data android:name="com.google.android.geo.API_KEY"
             android:value="${MAPS_KEY}"/>
  ```
- [ ] Commit: `"feat: flutter app, 5 screens scaffold, navigation, provider setup"`

### ✅ End of Day Deliverable
Flutter app running on emulator with all 5 screens navigable.

---

## Day 2 – Action Planning Agent + Crisis Feed Screen

### Backend: Action Planning Agent
- [ ] Open `/backend/routers/plan.py`. Implement **POST /plan/actions**
- [ ] Write action generation rules as a Python dictionary mapping:
  - **FLOOD + HIGH/CRITICAL**: `reroute_traffic`, `dispatch_rescue_boats`, `send_flood_alert`, `open_relief_camp`
  - **HEATWAVE + HIGH**: `send_heat_advisory`, `open_cooling_centres`, `restrict_outdoor_activity`
  - **BLOCKAGE + MEDIUM/HIGH**: `reroute_traffic`, `dispatch_traffic_police`, `update_navigation_apps`
  - **ACCIDENT + HIGH**: `dispatch_ambulance`, `dispatch_fire_brigade`, `close_road_segment`

### Flutter: Crisis Feed Screen
- [ ] `FutureBuilder` fetching `GET /detect/crisis` on load
- [ ] `ListView.builder` with custom `CrisisCard` widget
- [ ] **CrisisCard** shows:
  - Coloured left border by severity
  - Crisis type icon (flood/heat/blockage)
  - Location text
  - Confidence percentage
  - Time since detected
- [ ] Tap card → push Crisis Detail screen with `CrisisAnalysis` data (action plan list)

### API Service Methods
- [ ] `Future<CrisisEvent> fetchLatestCrisis()`
- [ ] `Future<ActionPlan> generateActionPlan(String eventId)`
- [ ] `Future<void> ingestSignal(String rawText)`
- [ ] Commit: `"feat: action planning agent + crisis feed and detail screens"`

### ✅ End of Day Deliverable
Action plans generated for all 4 crisis types. Crisis feed screen live and showing data.

---

## Day 3 – Mobile Map & Alerts Screens

### Map Screen (`map_screen.dart`)
- [ ] `GoogleMap` widget: `initialCameraPosition` set to Islamabad (lat: 33.6844, lng: 73.0479, zoom: 12)
- [ ] On screen load: call `api_service.fetchMapOverlay()` → parse GeoJSON response
- [ ] Add **Marker** at crisis location (red pin with crisis type label)
- [ ] Add red **Polyline** for blocked primary route (`width: 6, color: Colors.red`)
- [ ] Add green **Polyline** for alternate route (`width: 6, color: Colors.green`)
- [ ] Add semi-transparent **Polygon** for affected area (red fill, 30% opacity)
- [ ] Bottom sheet: shows crisis summary, affected routes, recommended alternate route name
- [ ] **FloatingActionButton** labelled "Run Simulation":
  - On press: call `api_service.runSimulation()` then refresh map to show updated (green) state

### Alerts Screen (`alerts_screen.dart`)
- [ ] Two tabs: **Alerts** and **Emergency Tickets**
- [ ] **Alerts tab**: `ListView` from `GET /simulate/alerts` – each card shows channel icon, message, area, time, recipient count badge
- [ ] **Tickets tab**: `ListView` from `GET /simulate/tickets` – each card shows unit, ETA countdown, status chip (OPEN/DISPATCHED/RESOLVED), location
- [ ] Pull-to-refresh on both tabs

### New API Service Methods
- [ ] `Future<MapOverlayData> fetchMapOverlay(String location)`
- [ ] `Future<SimulationResult> runSimulation(ActionPlan plan)`
- [ ] `Future<List<Alert>> fetchAlerts()`
- [ ] `Future<List<EmergencyTicket>> fetchTickets()`
- [ ] Commit: `"feat: map screen with crisis overlay, run simulation button, alerts and tickets screens"`

### ✅ End of Day Deliverable
Map shows crisis overlays. Pressing "Run Simulation" updates map to green state. Alerts/tickets visible.

---

## Day 4 – Agent Trace Screen & E2E Testing

### Trace Screen (`trace_screen.dart`)
- [ ] Call `GET /trace/latest` on load. Show `CircularProgressIndicator` while loading
- [ ] Render a **vertical Stepper** with 5 steps (one per agent)
- [ ] Each step has:
  - Agent name as title
  - Step description as subtitle
  - Duration badge
  - Expandable content showing input/output JSON in monospace font
- [ ] Steps automatically mark as "complete" (`StepState.complete`) based on trace data
- [ ] Auto-refresh button (or 5-second auto-poll) to update after new pipeline runs

### 5 End-to-End Test Scenarios
Document results in `/docs/TEST_RESULTS.md`:

| # | Scenario | Input | Verify |
|---|---|---|---|
| 1 | **Urdu Flood (G-10)** | Urdu text | `crisis_type=FLOOD`, confidence>0.7, reroute action generated, map route turns green |
| 2 | **English Heatwave** | English heatwave signal | `crisis_type=HEATWAVE`, cooling centres opened |
| 3 | **Multi-Source Flood** | Social + weather + traffic signals | CRITICAL severity, confidence>0.85, all 4 flood actions triggered |
| 4 | **Road Blockage** | Accident signal | BLOCKAGE/ACCIDENT detected, police dispatch ticket created |
| 5 | **Low Confidence** | Single vague signal | LOW severity, no critical actions triggered |

- [ ] Commit: `"feat: agent trace screen, all 5 e2e test scenarios documented and passing"`

### ✅ End of Day Deliverable
All 5 scenarios pass. Trace screen shows complete reasoning pipeline.

---

## Day 5 – Demo Dry Run, APK Build & Submission

### Demo Dry Run (Morning)
- [ ] Run through the full demo script 3 times solo. Time each section
- [ ] Reset system state: call `POST /simulate/reset`. Verify clean slate
- [ ] Ensure phone is connected to same WiFi as backend
- [ ] Update `api_service.dart` base URL to use machine's local IP (e.g. `http://192.168.1.X:8000`) not `10.0.2.2`
- [ ] Test Urdu signal input on physical device

### APK Build
- [ ] Build release APK: `flutter build apk --release`
- [ ] Find APK at `build/app/outputs/flutter-apk/app-release.apk`
- [ ] Install APK on a fresh device (not the dev device). Run demo scenario. Confirm no crashes

### Screenshots
- [ ] Take screenshots of key moments:
  - Crisis card
  - Map before simulation
  - Map after simulation
  - Dashboard outcome
  - Trace screen
- [ ] Save screenshots to `/docs/DEMO_SCREENSHOTS/` with descriptive names

### Demo Recording (Afternoon – All Members)
- [ ] Join Google Meet. Role: **Run mobile app** during recording
- [ ] Participate in 3 recording takes
- [ ] Assist with final submission

### ✅ End of Day Deliverable
APK built, dry run complete, screenshots captured. Demo recorded and submitted.

---

## Dependencies & Coordination Points
| With | What | When |
|---|---|---|
| **Hasnain** | FastAPI endpoints must be live for API calls | Day 1 → Day 2 |
| **Arshman** | Pydantic models must match Dart models | Day 1 → Day 2 |
| **Hasnain** | Maps overlay endpoint needed for map screen | Day 3 |
| **Anas** | Simulation engine endpoint needed for "Run Simulation" | Day 3 |
| **Shayan** | Trace endpoint needed for trace screen | Day 3 → Day 4 |
| **Anas** | Outcome summary endpoint needed for home dashboard | Day 4 |
