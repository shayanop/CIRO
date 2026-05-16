// CIRO data models — mirrors backend Pydantic schemas

class RawSignalInput {
  final String source;
  final String text;
  final Map<String, dynamic>? metadata;

  RawSignalInput({required this.source, required this.text, this.metadata});

  Map<String, dynamic> toJson() => {
        'source': source,
        'text': text,
        if (metadata != null) 'metadata': metadata,
      };
}

class Signal {
  final String signalId;
  final String source;
  final String content;
  final String? location;
  final String timestamp;
  final String? language;
  final String? severityHint;
  final List<String> keywords;

  Signal({
    required this.signalId,
    required this.source,
    required this.content,
    this.location,
    required this.timestamp,
    this.language,
    this.severityHint,
    required this.keywords,
  });

  factory Signal.fromJson(Map<String, dynamic> j) => Signal(
        signalId: j['signal_id'] ?? '',
        source: j['source'] ?? '',
        content: j['content'] ?? '',
        location: j['location'],
        timestamp: j['timestamp'] ?? '',
        language: j['language'],
        severityHint: j['severity_hint'],
        keywords: List<String>.from(j['keywords'] ?? []),
      );
}

class SignalBatch {
  final String batchId;
  final List<Signal> signals;
  final String? primaryLocation;

  SignalBatch({required this.batchId, required this.signals, this.primaryLocation});

  factory SignalBatch.fromJson(Map<String, dynamic> j) => SignalBatch(
        batchId: j['batch_id'] ?? '',
        signals: (j['signals'] as List? ?? []).map((s) => Signal.fromJson(s)).toList(),
        primaryLocation: j['primary_location'],
      );
}

class CrisisEvent {
  final String eventId;
  final String crisisType;
  final String location;
  final double confidence;
  final String severity;
  final List<Signal> signals;
  final String explanation;
  final String detectedAt;

  CrisisEvent({
    required this.eventId,
    required this.crisisType,
    required this.location,
    required this.confidence,
    required this.severity,
    required this.signals,
    required this.explanation,
    required this.detectedAt,
  });

  factory CrisisEvent.fromJson(Map<String, dynamic> j) => CrisisEvent(
        eventId: j['event_id'] ?? '',
        crisisType: j['crisis_type'] ?? '',
        location: j['location'] ?? '',
        confidence: (j['confidence'] as num?)?.toDouble() ?? 0.0,
        severity: j['severity'] ?? 'low',
        signals: (j['signals'] as List? ?? []).map((s) => Signal.fromJson(s)).toList(),
        explanation: j['explanation'] ?? '',
        detectedAt: j['detected_at'] ?? '',
      );
}

class CrisisAnalysis {
  final String analysisId;
  final String eventId;
  final List<String> impact;
  final int affectedPopulation;
  final List<String> infrastructureAtRisk;
  final String urgency;
  final String summary;

  CrisisAnalysis({
    required this.analysisId,
    required this.eventId,
    required this.impact,
    required this.affectedPopulation,
    required this.infrastructureAtRisk,
    required this.urgency,
    required this.summary,
  });

  factory CrisisAnalysis.fromJson(Map<String, dynamic> j) => CrisisAnalysis(
        analysisId: j['analysis_id'] ?? '',
        eventId: j['event_id'] ?? '',
        impact: List<String>.from(j['impact'] ?? []),
        affectedPopulation: j['affected_population'] ?? 0,
        infrastructureAtRisk: List<String>.from(j['infrastructure_at_risk'] ?? []),
        urgency: j['urgency'] ?? 'monitoring',
        summary: j['summary'] ?? '',
      );
}

class EmergencyTicket {
  final String ticketId;
  final String crisisType;
  final String location;
  final String unitDispatched;
  final int etaMinutes;
  String status;
  final String createdAt;

  EmergencyTicket({
    required this.ticketId,
    required this.crisisType,
    required this.location,
    required this.unitDispatched,
    required this.etaMinutes,
    required this.status,
    required this.createdAt,
  });

  factory EmergencyTicket.fromJson(Map<String, dynamic> j) => EmergencyTicket(
        ticketId: j['ticket_id'] ?? '',
        crisisType: j['crisis_type'] ?? '',
        location: j['location'] ?? '',
        unitDispatched: j['unit_dispatched'] ?? '',
        etaMinutes: j['eta_minutes'] ?? 0,
        status: j['status'] ?? 'open',
        createdAt: j['created_at'] ?? '',
      );
}

class CiroAlert {
  final String alertId;
  final String message;
  final String targetArea;
  final String channel;
  final String sentAt;
  final int recipientsCount;

  CiroAlert({
    required this.alertId,
    required this.message,
    required this.targetArea,
    required this.channel,
    required this.sentAt,
    required this.recipientsCount,
  });

  factory CiroAlert.fromJson(Map<String, dynamic> j) => CiroAlert(
        alertId: j['alert_id'] ?? '',
        message: j['message'] ?? '',
        targetArea: j['target_area'] ?? '',
        channel: j['channel'] ?? 'push',
        sentAt: j['sent_at'] ?? '',
        recipientsCount: j['recipients_count'] ?? 0,
      );
}

class SimulationResult {
  final String runId;
  final List<String> actionsExecuted;
  final List<EmergencyTicket> ticketsCreated;
  final List<CiroAlert> alertsSent;

  SimulationResult({
    required this.runId,
    required this.actionsExecuted,
    required this.ticketsCreated,
    required this.alertsSent,
  });

  factory SimulationResult.fromJson(Map<String, dynamic> j) => SimulationResult(
        runId: j['run_id'] ?? '',
        actionsExecuted: List<String>.from(j['actions_executed'] ?? []),
        ticketsCreated: (j['tickets_created'] as List? ?? [])
            .map((t) => EmergencyTicket.fromJson(t))
            .toList(),
        alertsSent:
            (j['alerts_sent'] as List? ?? []).map((a) => CiroAlert.fromJson(a)).toList(),
      );
}

class OutcomeSummary {
  final double congestionReductionPct;
  final int vehiclesRerouted;
  final int minEtaMinutes;
  final int alertsDispatched;
  final int ticketsCreated;
  final List<String> resourcesOpened;

  OutcomeSummary({
    required this.congestionReductionPct,
    required this.vehiclesRerouted,
    required this.minEtaMinutes,
    required this.alertsDispatched,
    required this.ticketsCreated,
    required this.resourcesOpened,
  });

  factory OutcomeSummary.fromJson(Map<String, dynamic> j) => OutcomeSummary(
        congestionReductionPct: (j['congestion_reduction_pct'] as num?)?.toDouble() ?? 0.0,
        vehiclesRerouted: j['vehicles_rerouted'] ?? 0,
        minEtaMinutes: j['min_eta_minutes'] ?? 0,
        alertsDispatched: j['alerts_dispatched'] ?? 0,
        ticketsCreated: j['tickets_created'] ?? 0,
        resourcesOpened: List<String>.from(j['resources_opened'] ?? []),
      );
}

class TraceStep {
  final String agent;
  final String step;
  final int durationMs;
  final Map<String, dynamic> input;
  final Map<String, dynamic> output;

  TraceStep({
    required this.agent,
    required this.step,
    required this.durationMs,
    required this.input,
    required this.output,
  });

  factory TraceStep.fromJson(Map<String, dynamic> j) => TraceStep(
        agent: j['agent'] ?? '',
        step: j['step'] ?? '',
        durationMs: j['duration_ms'] ?? 0,
        input: Map<String, dynamic>.from(j['input'] ?? {}),
        output: Map<String, dynamic>.from(j['output'] ?? {}),
      );
}

class PipelineResult {
  final String runId;
  final SignalBatch batch;
  final CrisisEvent event;
  final CrisisAnalysis analysis;
  final SimulationResult simulation;

  PipelineResult({
    required this.runId,
    required this.batch,
    required this.event,
    required this.analysis,
    required this.simulation,
  });

  factory PipelineResult.fromJson(Map<String, dynamic> j) => PipelineResult(
        runId: j['run_id'] ?? '',
        batch: SignalBatch.fromJson(j['batch'] ?? {}),
        event: CrisisEvent.fromJson(j['event'] ?? {}),
        analysis: CrisisAnalysis.fromJson(j['analysis'] ?? {}),
        simulation: SimulationResult.fromJson(j['simulation'] ?? {}),
      );
}

class MapOverlay {
  final Map<String, dynamic>? crisisPin;
  final List<Map<String, dynamic>> affectedPolygon;
  final Map<String, dynamic>? primaryRoute;
  final Map<String, dynamic>? alternateRoute;

  MapOverlay({
    this.crisisPin,
    required this.affectedPolygon,
    this.primaryRoute,
    this.alternateRoute,
  });

  factory MapOverlay.fromJson(Map<String, dynamic> j) => MapOverlay(
        crisisPin: j['crisis_pin'] != null ? Map<String, dynamic>.from(j['crisis_pin']) : null,
        affectedPolygon: (j['affected_polygon'] as List? ?? [])
            .map((p) => Map<String, dynamic>.from(p))
            .toList(),
        primaryRoute:
            j['primary_route'] != null ? Map<String, dynamic>.from(j['primary_route']) : null,
        alternateRoute:
            j['alternate_route'] != null ? Map<String, dynamic>.from(j['alternate_route']) : null,
      );
}
