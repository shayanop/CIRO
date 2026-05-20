# CIRO Flutter App

Mobile client for **CIRO — Crisis Intelligence & Response Orchestrator**.

Full project documentation: [../../README.md](../../README.md)

---

## Screens

| Tab | File | Purpose |
|-----|------|---------|
| Home | `lib/screens/home_screen.dart` | Pipeline FAB, before/after outcome |
| Crisis | `lib/screens/crisis_feed_screen.dart` | Trace history cards |
| Map | `lib/screens/map_screen.dart` | GeoJSON overlay + routes |
| Alerts | `lib/screens/alerts_screen.dart` | Tickets & alerts (badge on new) |
| Trace | `lib/screens/trace_screen.dart` | 5-agent stepper |

State: `lib/services/app_state.dart` · API: `lib/services/api_client.dart` · Theme: `lib/theme.dart`

---

## Setup

```bash
cd frontend/ciro_app
flutter pub get
flutter run
```

### Backend URL

| Environment | Default |
|-------------|---------|
| Android emulator | `http://10.0.2.2:8000` |
| Web / iOS simulator | `http://localhost:8000` |
| Physical device | Your PC LAN IP (see `start_server.bat` output) |

Change in-app via server settings — stored in `SharedPreferences` (`lib/services/config.dart`).

---

## API integration

- `POST /pipeline/run` — main demo trigger
- `GET /trace/history` — crisis feed (bare JSON array)
- `GET /simulate/alerts/version` — polled every **2s**; refreshes tickets/alerts on change
- `GET /simulate/tickets`, `/simulate/alerts` — bare arrays
- `GET /maps/crisis-overlay` — map layers

---

## Tests

```bash
flutter test
```

Widget smoke test: `test/widget_test.dart`.
