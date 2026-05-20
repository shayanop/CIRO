import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';
import 'config.dart';

class ApiClient {
  static String get baseUrl => Config.baseUrl;

  // ── Raw helpers ────────────────────────────────────────────────────────────

  static Future<dynamic> _getRaw(String path) async {
    final res = await http
        .get(Uri.parse('$baseUrl$path'))
        .timeout(const Duration(seconds: 10));
    if (res.statusCode >= 400) throw Exception('GET $path → ${res.statusCode}');
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> _get(String path) async {
    final raw = await _getRaw(path);
    if (raw is Map<String, dynamic>) return raw;
    return {'data': raw};
  }

  static Future<Map<String, dynamic>> _post(
      String path, Map<String, dynamic> body) async {
    final res = await http
        .post(
          Uri.parse('$baseUrl$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 15));
    if (res.statusCode >= 400) {
      throw Exception('POST $path → ${res.statusCode}: ${res.body}');
    }
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> _patch(
      String path, Map<String, dynamic> body) async {
    final res = await http
        .patch(
          Uri.parse('$baseUrl$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 10));
    if (res.statusCode >= 400) throw Exception('PATCH $path → ${res.statusCode}');
    return jsonDecode(res.body);
  }

  // ── Endpoints ──────────────────────────────────────────────────────────────

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
    final raw = await _getRaw('/trace/history');
    final List items;
    if (raw is List) {
      items = raw;
    } else if (raw is Map) {
      items = (raw['runs'] ?? raw['data'] ?? []) as List;
    } else {
      items = [];
    }
    return items.map((r) => Map<String, dynamic>.from(r)).toList();
  }

  static Future<Map<String, dynamic>> getAlertsVersion() async {
    return _get('/simulate/alerts/version');
  }

  // Simulation — backend returns a bare JSON array, NOT a dict
  static Future<List<EmergencyTicket>> getTickets() async {
    final raw = await _getRaw('/simulate/tickets');
    List items;
    if (raw is List) {
      items = raw;
    } else if (raw is Map) {
      items = (raw['tickets'] ?? raw['data'] ?? []) as List;
    } else {
      items = [];
    }
    return items.map((t) => EmergencyTicket.fromJson(t)).toList();
  }

  static Future<List<CiroAlert>> getAlerts() async {
    final raw = await _getRaw('/simulate/alerts');
    List items;
    if (raw is List) {
      items = raw;
    } else if (raw is Map) {
      items = (raw['alerts'] ?? raw['data'] ?? []) as List;
    } else {
      items = [];
    }
    return items.map((a) => CiroAlert.fromJson(a)).toList();
  }

  static Future<void> updateTicketStatus(String ticketId, String status) async {
    await _patch('/simulate/tickets/$ticketId/status', {'status': status});
  }

  static Future<void> resetSimulation() async {
    await _post('/simulate/reset', {});
  }

  // Maps
  static Future<MapOverlay> getCrisisOverlay(String location) async {
    final j = await _get(
        '/maps/crisis-overlay?location=${Uri.encodeComponent(location)}');
    return MapOverlay.fromJson(j);
  }

  // Mock social feed
  static Future<List<Map<String, dynamic>>> getMockSocial() async {
    final j = await _get('/mock/social');
    return List<Map<String, dynamic>>.from(j['signals'] ?? j['data'] ?? [j]);
  }
}
