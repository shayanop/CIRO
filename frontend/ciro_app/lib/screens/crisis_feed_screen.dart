import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';
import '../theme.dart';

const _crisisIcons = {
  'flood'         : Icons.water_rounded,
  'heatwave'      : Icons.wb_sunny_rounded,
  'blockage'      : Icons.traffic_rounded,
  'accident'      : Icons.car_crash_rounded,
  'infrastructure': Icons.construction_rounded,
  'fire'          : Icons.local_fire_department_rounded,
  'earthquake'    : Icons.crisis_alert_rounded,
  'storm'         : Icons.thunderstorm_rounded,
};

class CrisisFeedScreen extends StatefulWidget {
  const CrisisFeedScreen({super.key});

  @override
  State<CrisisFeedScreen> createState() => _CrisisFeedScreenState();
}

class _CrisisFeedScreenState extends State<CrisisFeedScreen> {
  List<Map<String, dynamic>> _runs = [];
  bool _loading = true;
  bool _hasError = false;
  Timer? _timer;
  Object? _lastPipelineResult;

  @override
  void initState() {
    super.initState();
    _fetch();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _fetch());
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final result = context.watch<AppState>().lastPipelineResult;
    if (result != null && !identical(result, _lastPipelineResult)) {
      _lastPipelineResult = result;
      _fetch();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetch() async {
    try {
      final runs = await ApiClient.getTraceHistory();
      if (mounted) setState(() { _runs = runs; _loading = false; _hasError = false; });
    } catch (_) {
      if (mounted) setState(() { _loading = false; _hasError = true; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        title: const Text('Crisis Feed'),
        actions: [
          // auto-refresh indicator
          Padding(
            padding: const EdgeInsets.only(right: 4),
            child: Tooltip(
              message: 'Auto-refreshing every 5 s',
              child: Icon(Icons.sync_rounded,
                  color: kAccent.withOpacity(0.6), size: 18),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _fetch,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: kPrimary))
          : _hasError
              ? _ErrorState(onRetry: _fetch)
              : _runs.isEmpty
                  ? const _EmptyState()
                  : RefreshIndicator(
                      color: kPrimary,
                      backgroundColor: kCard,
                      onRefresh: _fetch,
                      child: ListView.builder(
                        padding: const EdgeInsets.fromLTRB(14, 14, 14, 24),
                        itemCount: _runs.length,
                        itemBuilder: (ctx, i) {
                          final run = _runs[_runs.length - 1 - i];
                          return _CrisisCard(run: run, isLatest: i == 0);
                        },
                      ),
                    ),
    );
  }
}

class _CrisisCard extends StatelessWidget {
  final Map<String, dynamic> run;
  final bool isLatest;
  const _CrisisCard({required this.run, required this.isLatest});

  @override
  Widget build(BuildContext context) {
    Map<String, dynamic>? eventOut;
    Map<String, dynamic>? reasonOut;

    if (run['crisis_type'] != null) {
      eventOut = {
        'crisis_type': run['crisis_type'],
        'location': run['location'],
        'severity': run['severity'],
        'confidence': run['confidence'],
        'explanation': run['explanation'],
      };
      reasonOut = {
        'summary': run['analysis_summary'],
        'impact': run['impact'],
      };
    } else {
      final steps = run['steps'] as List? ?? [];
      for (final s in steps) {
        final agent = (s['agent'] ?? '').toString();
        final step = (s['step'] ?? '').toString();
        if (agent.contains('detect') || step.contains('detect')) {
          eventOut = s['output'] as Map<String, dynamic>?;
        }
        if (agent.contains('reason') || step.contains('reason')) {
          reasonOut = s['output'] as Map<String, dynamic>?;
        }
      }
    }

    final crisisType = eventOut?['crisis_type'] ?? 'unknown';
    final location = eventOut?['location'] ?? 'Unknown';
    final severity = eventOut?['severity'] ?? 'low';
    final confidence = (eventOut?['confidence'] as num?)?.toDouble() ?? 0.0;
    final explanation = eventOut?['explanation'] ?? '';
    final summary = reasonOut?['summary'] ?? '';
    final impact = List<String>.from(reasonOut?['impact'] ?? []);

    final color = severityColors[severity] ?? Colors.grey;
    final icon  = _crisisIcons[crisisType] ?? Icons.warning_rounded;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: kCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isLatest ? color.withOpacity(0.5) : kCardBorder,
          width: isLatest ? 1.5 : 1,
        ),
        boxShadow: isLatest
            ? [BoxShadow(color: color.withOpacity(0.12), blurRadius: 16)]
            : [],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => _showDetails(context, crisisType, location, severity,
            confidence, explanation, summary, impact),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(icon, color: color, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                '${crisisType.toString().toUpperCase()}',
                                style: TextStyle(
                                    color: color,
                                    fontWeight: FontWeight.w800,
                                    fontSize: 13,
                                    letterSpacing: 0.5),
                              ),
                            ),
                            _SeverityChip(severity),
                            if (isLatest) ...[
                              const SizedBox(width: 6),
                              _LatestBadge(),
                            ],
                          ],
                        ),
                        const SizedBox(height: 3),
                        Row(
                          children: [
                            const Icon(Icons.location_on_rounded,
                                size: 12, color: Colors.white38),
                            const SizedBox(width: 4),
                            Text(location,
                                style: const TextStyle(
                                    color: Colors.white54, fontSize: 12)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Confidence bar
              _ConfidenceBar(value: confidence, color: color),
              if (explanation.isNotEmpty) ...[
                const SizedBox(height: 10),
                Text(explanation,
                    style: const TextStyle(
                        color: Colors.white54, fontSize: 12, height: 1.4),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis),
              ],
              const SizedBox(height: 10),
              Row(
                children: [
                  const Icon(Icons.chevron_right_rounded,
                      color: kPrimary, size: 14),
                  const Text('Tap for full analysis',
                      style: TextStyle(color: kPrimary, fontSize: 11)),
                  const Spacer(),
                  Text('${(run['steps'] as List? ?? []).length} agent steps',
                      style: const TextStyle(
                          color: Colors.white24, fontSize: 11)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showDetails(
      BuildContext context,
      String crisisType,
      String location,
      String severity,
      double confidence,
      String explanation,
      String summary,
      List<String> impact) {
    final color = severityColors[severity] ?? Colors.grey;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.6,
        maxChildSize: 0.92,
        builder: (_, ctrl) => Container(
          decoration: const BoxDecoration(
            color: kSurface,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: ListView(
            controller: ctrl,
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(_crisisIcons[crisisType] ?? Icons.warning_rounded,
                        color: color, size: 24),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(crisisType.toUpperCase(),
                            style: TextStyle(
                                color: color,
                                fontWeight: FontWeight.w800,
                                fontSize: 18,
                                letterSpacing: 1)),
                        Text(location,
                            style: const TextStyle(
                                color: Colors.white60, fontSize: 14)),
                      ],
                    ),
                  ),
                  _SeverityChip(severity),
                ],
              ),
              const SizedBox(height: 20),
              _ConfidenceBar(value: confidence, color: color),
              const SizedBox(height: 20),
              if (summary.isNotEmpty) ...[
                _SheetLabel('SUMMARY'),
                const SizedBox(height: 8),
                Text(summary,
                    style: const TextStyle(
                        color: Colors.white70, fontSize: 13, height: 1.6)),
                const SizedBox(height: 16),
              ],
              if (impact.isNotEmpty) ...[
                _SheetLabel('IMPACT ASSESSMENT'),
                const SizedBox(height: 8),
                ...impact.map((pt) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Padding(
                            padding: EdgeInsets.only(top: 2),
                            child: Icon(Icons.arrow_right_rounded,
                                color: kPrimary, size: 16),
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(pt,
                                style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 13,
                                    height: 1.4)),
                          ),
                        ],
                      ),
                    )),
                const SizedBox(height: 16),
              ],
              if (explanation.isNotEmpty) ...[
                _SheetLabel('DETECTION EXPLANATION'),
                const SizedBox(height: 8),
                Text(explanation,
                    style: const TextStyle(
                        color: Colors.white54, fontSize: 13, height: 1.5)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double value;
  final Color color;
  const _ConfidenceBar({required this.value, required this.color});

  @override
  Widget build(BuildContext context) => Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('CONFIDENCE',
                  style: TextStyle(
                      color: Colors.white38,
                      fontSize: 10,
                      letterSpacing: 1,
                      fontWeight: FontWeight.w600)),
              Text('${(value * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                      color: color,
                      fontSize: 12,
                      fontWeight: FontWeight.w800)),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: value,
              minHeight: 5,
              backgroundColor: Colors.white.withOpacity(0.06),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      );
}

class _SeverityChip extends StatelessWidget {
  final String severity;
  const _SeverityChip(this.severity);

  @override
  Widget build(BuildContext context) {
    final c = severityColors[severity] ?? Colors.grey;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: c.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: c.withOpacity(0.5)),
      ),
      child: Text(severity.toUpperCase(),
          style: TextStyle(
              color: c,
              fontSize: 9,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.8)),
    );
  }
}

class _LatestBadge extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
        decoration: BoxDecoration(
          color: kPrimary.withOpacity(0.15),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: kPrimary.withOpacity(0.4)),
        ),
        child: const Text('LATEST',
            style: TextStyle(
                color: kPrimary,
                fontSize: 8,
                fontWeight: FontWeight.w800,
                letterSpacing: 1)),
      );
}

Widget _SheetLabel(String text) => Text(text,
    style: const TextStyle(
        color: Colors.white38,
        fontSize: 10,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.5));

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.radar_rounded, size: 64, color: Colors.white12),
            const SizedBox(height: 16),
            const Text('No crises detected yet',
                style: TextStyle(
                    color: Colors.white54,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            const Text('Trigger the pipeline from the Home tab',
                style: TextStyle(color: Colors.white24, fontSize: 13)),
          ],
        ),
      );
}

class _ErrorState extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorState({required this.onRetry});

  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_rounded, size: 52, color: kDanger),
            const SizedBox(height: 12),
            const Text('Cannot reach backend',
                style: TextStyle(color: Colors.white54, fontSize: 15)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('RETRY'),
            ),
          ],
        ),
      );
}
