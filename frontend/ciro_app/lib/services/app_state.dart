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

  Future<void> checkHealth() async {
    try {
      await ApiClient.health();
      isOnline = true;
    } catch (_) {
      isOnline = false;
    }
    notifyListeners();
  }

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

  Future<void> refreshAll() async {
    await Future.wait([
      _loadOutcome(),
      _loadTrace(),
      _loadTickets(),
      _loadAlerts(),
    ]);
  }

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
}
