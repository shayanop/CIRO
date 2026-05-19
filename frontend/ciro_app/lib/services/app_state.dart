import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/models.dart';
import 'api_client.dart';

class AppState extends ChangeNotifier {
  bool isOnline = false;
  bool isPipelineRunning = false;
  PipelineResult? lastPipelineResult;
  OutcomeSummary? outcomeSummary;
  List<TraceStep> latestTrace = [];
  List<EmergencyTicket> tickets = [];
  List<CiroAlert> alerts = [];
  String? error;

  // Real-time polling
  Timer? _pollTimer;
  bool _isPolling = false;
  int newAlertsCount = 0; // badge counter
  int _lastAlertCount = 0;

  AppState() {
    _startPolling();
  }

  // ── Polling ──────────────────────────────────────────────────────────────

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 4), (_) => _poll());
    _poll(); // immediate first fetch
  }

  Future<void> _poll() async {
    if (_isPolling) return;
    _isPolling = true;
    try {
      await Future.wait([_loadAlerts(), _loadTickets()]);
      // detect new alerts for badge
      if (alerts.length > _lastAlertCount) {
        newAlertsCount += alerts.length - _lastAlertCount;
        _lastAlertCount = alerts.length;
        notifyListeners();
      }
    } finally {
      _isPolling = false;
    }
  }

  void clearAlertBadge() {
    newAlertsCount = 0;
    notifyListeners();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  // ── Health ───────────────────────────────────────────────────────────────

  Future<void> checkHealth() async {
    try {
      await ApiClient.health();
      isOnline = true;
    } catch (_) {
      isOnline = false;
    }
    notifyListeners();
  }

  // ── Pipeline ─────────────────────────────────────────────────────────────

  Future<PipelineResult?> runPipeline(RawSignalInput input) async {
    isPipelineRunning = true;
    error = null;
    notifyListeners();
    try {
      final result = await ApiClient.runPipeline(input);
      lastPipelineResult = result;
      isPipelineRunning = false;
      notifyListeners();
      await refreshAll();
      return result;
    } catch (e) {
      error = e.toString();
      isPipelineRunning = false;
      notifyListeners();
      return null;
    }
  }

  // ── Full Refresh ─────────────────────────────────────────────────────────

  Future<void> refreshAll() async {
    await Future.wait([
      _loadOutcome(),
      _loadTrace(),
      _loadTickets(),
      _loadAlerts(),
    ]);
    _lastAlertCount = alerts.length;
  }

  // ── Individual Loaders ───────────────────────────────────────────────────

  Future<void> _loadOutcome() async {
    try {
      outcomeSummary = await ApiClient.getOutcomeSummary();
    } catch (_) {}
    notifyListeners();
  }

  Future<void> _loadTrace() async {
    try {
      latestTrace = await ApiClient.getLatestTrace();
    } catch (_) {}
    notifyListeners();
  }

  Future<void> _loadTickets() async {
    try {
      tickets = await ApiClient.getTickets();
    } catch (_) {}
    notifyListeners();
  }

  Future<void> _loadAlerts() async {
    try {
      alerts = await ApiClient.getAlerts();
    } catch (_) {}
    notifyListeners();
  }

  // ── Ticket Status ────────────────────────────────────────────────────────

  Future<void> updateTicketStatus(String ticketId, String status) async {
    try {
      await ApiClient.updateTicketStatus(ticketId, status);
      final idx = tickets.indexWhere((t) => t.ticketId == ticketId);
      if (idx != -1) {
        tickets[idx].status = status;
        notifyListeners();
      }
    } catch (e) {
      error = e.toString();
      notifyListeners();
    }
  }

  // ── Reset ────────────────────────────────────────────────────────────────

  Future<void> resetAll() async {
    try {
      await ApiClient.resetSimulation();
      tickets = [];
      alerts = [];
      outcomeSummary = null;
      latestTrace = [];
      lastPipelineResult = null;
      newAlertsCount = 0;
      _lastAlertCount = 0;
      error = null;
      notifyListeners();
    } catch (e) {
      error = e.toString();
      notifyListeners();
    }
  }
}
