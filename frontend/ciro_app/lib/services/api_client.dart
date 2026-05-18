import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiClient {
  static const String baseUrl = bool.hasEnvironment('CIRO_API')
      ? String.fromEnvironment('CIRO_API')
      : (kIsWeb ? 'http://localhost:8000' : 'http://10.0.2.2:8000');

  static Future<Map<String, dynamic>> _get(String path) async {
    final res = await http.get(Uri.parse('$baseUrl$path'));
    if (res.statusCode >= 400) throw Exception('GET $path → ${res.statusCode}');
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final res = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (res.statusCode >= 400) throw Exception('POST $path → ${res.statusCode}: ${res.body}');
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> _patch(String path, Map<String, dynamic> body) async {
    final res = await http.patch(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (res.statusCode >= 400) throw Exception('PATCH $path → ${res.statusCode}');
    return jsonDecode(res.body);
  }

  // Health
  static Future<Map<String, dynamic>> health() => _get('/health');

  // Pipeline
  static Future<PipelineResult> runPipeline(RawSignalInput input) async {
    final j = await _post('/pipeline/run', input.toJson());
    return PipelineResult.fromJson(j);
  }

  // Ingest
  static Future<SignalBatch> ingestSignal(RawSignalInput input) async {
    final j = await _post('/ingest/signal', input.toJson());
    return SignalBatch.fromJson(j);
  }

  // Outcome
  static Future<OutcomeSummary> getOutcomeSummary() async {
    final j = await _get('/outcome/summary');
    return OutcomeSummary.fromJson(j);
  }

  // Trace
  static Future<List<TraceStep>> getLatestTrace() async {
    final j = await _get('/trace/latest');
    final steps = j['steps'] as List? ?? [];
    return steps.map((s) => TraceStep.fromJson(s)).toList();
  }

  static Future<List<Map<String, dynamic>>> getTraceHistory() async {
    final j = await _get('/trace/history');
    final runs = j['runs'] as List? ?? [];
    return runs.map((r) => Map<String, dynamic>.from(r)).toList();
  }

  // Simulation
  static Future<List<EmergencyTicket>> getTickets() async {
    final j = await _get('/simulate/tickets');
    final items = j['tickets'] as List? ?? [];
    return items.map((t) => EmergencyTicket.fromJson(t)).toList();
  }

  static Future<List<CiroAlert>> getAlerts() async {
    final j = await _get('/simulate/alerts');
    final items = j['alerts'] as List? ?? [];
    return items.map((a) => CiroAlert.fromJson(a)).toList();
  }

  static Future<void> updateTicketStatus(String ticketId, String status) async {
    await _patch('/simulate/tickets/$ticketId/status', {'status': status});
  }

  // Maps
  static Future<MapOverlay> getCrisisOverlay(String location) async {
    final j = await _get('/maps/crisis-overlay?location=${Uri.encodeComponent(location)}');
    return MapOverlay.fromJson(j);
  }

  // Mock social feed
  static Future<List<Map<String, dynamic>>> getMockSocial() async {
    final j = await _get('/mock/social');
    return List<Map<String, dynamic>>.from(j['signals'] ?? j['data'] ?? [j]);
  }
}
