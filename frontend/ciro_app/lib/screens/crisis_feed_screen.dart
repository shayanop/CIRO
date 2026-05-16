import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_client.dart';
import '../theme.dart';

const _crisisIcons = {
  'flood': Icons.water,
  'heatwave': Icons.wb_sunny,
  'blockage': Icons.traffic,
  'accident': Icons.car_crash,
  'infrastructure': Icons.construction,
  'fire': Icons.local_fire_department,
  'earthquake': Icons.crisis_alert,
  'storm': Icons.thunderstorm,
};

class CrisisFeedScreen extends StatefulWidget {
  const CrisisFeedScreen({super.key});

  @override
  State<CrisisFeedScreen> createState() => _CrisisFeedScreenState();
}

class _CrisisFeedScreenState extends State<CrisisFeedScreen> {
  List<Map<String, dynamic>> _runs = [];
  bool _loading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetch();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _fetch());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetch() async {
    try {
      final runs = await ApiClient.getTraceHistory();
      if (mounted) setState(() { _runs = runs; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Crisis Feed'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetch),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _runs.isEmpty
              ? const Center(child: Text('No crises detected yet.\nTrigger the pipeline from Home.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white38)))
              : RefreshIndicator(
                  onRefresh: _fetch,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _runs.length,
                    itemBuilder: (ctx, i) {
                      final run = _runs[_runs.length - 1 - i];
                      return _CrisisCard(run: run);
                    },
                  ),
                ),
    );
  }
}

class _CrisisCard extends StatelessWidget {
  final Map<String, dynamic> run;
  const _CrisisCard({required this.run});

  @override
  Widget build(BuildContext context) {
    final steps = run['steps'] as List? ?? [];
    Map<String, dynamic>? eventStep;
    Map<String, dynamic>? reasonStep;
    for (final s in steps) {
      if ((s['agent'] ?? '').toString().contains('detect') || (s['step'] ?? '').toString().contains('detect')) {
        eventStep = s;
      }
      if ((s['agent'] ?? '').toString().contains('reason') || (s['step'] ?? '').toString().contains('reason')) {
        reasonStep = s;
      }
    }

    final output = eventStep?['output'] as Map<String, dynamic>? ?? {};
    final crisisType = output['crisis_type'] ?? 'unknown';
    final location = output['location'] ?? 'Unknown';
    final severity = output['severity'] ?? 'low';
    final confidence = (output['confidence'] as num?)?.toDouble() ?? 0.0;
    final explanation = output['explanation'] ?? '';

    final reasonOut = reasonStep?['output'] as Map<String, dynamic>? ?? {};
    final summary = reasonOut['summary'] ?? '';
    final impact = List<String>.from(reasonOut['impact'] ?? []);

    final color = severityColors[severity] ?? Colors.grey;
    final icon = _crisisIcons[crisisType] ?? Icons.warning;

    return Card(
      color: const Color(0xFF1C2340),
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _showDetails(context, crisisType, location, severity, confidence, explanation, summary, impact, reasonOut),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: color.withOpacity(0.15),
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
                            '${crisisType.toString().toUpperCase()} · $location',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                        ),
                        _SeverityChip(severity),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Text('Confidence: ', style: TextStyle(color: Colors.white38, fontSize: 11)),
                        Text('${(confidence * 100).toStringAsFixed(0)}%', style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    if (explanation.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(explanation, style: const TextStyle(color: Colors.white60, fontSize: 12), maxLines: 2, overflow: TextOverflow.ellipsis),
                    ],
                    const SizedBox(height: 6),
                    const Text('Tap for details →', style: TextStyle(color: Color(0xFF00D4FF), fontSize: 11)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showDetails(BuildContext context, String crisisType, String location, String severity, double confidence, String explanation, String summary, List<String> impact, Map<String, dynamic> reasonOut) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF141929),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        builder: (_, ctrl) => ListView(
          controller: ctrl,
          padding: const EdgeInsets.all(20),
          children: [
            Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)))),
            const SizedBox(height: 16),
            Text('${crisisType.toUpperCase()} — $location', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 8),
            _SeverityChip(severity),
            const SizedBox(height: 12),
            Text('Confidence: ${(confidence * 100).toStringAsFixed(1)}%', style: const TextStyle(color: Colors.white60)),
            const SizedBox(height: 8),
            if (summary.isNotEmpty) ...[
              const Text('SUMMARY', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
              const SizedBox(height: 4),
              Text(summary, style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 12),
            ],
            if (impact.isNotEmpty) ...[
              const Text('IMPACT', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
              const SizedBox(height: 4),
              ...impact.map((i) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(children: [const Text('• ', style: TextStyle(color: Color(0xFF00D4FF))), Expanded(child: Text(i, style: const TextStyle(color: Colors.white70)))]),
              )),
              const SizedBox(height: 12),
            ],
            if (explanation.isNotEmpty) ...[
              const Text('EXPLANATION', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
              const SizedBox(height: 4),
              Text(explanation, style: const TextStyle(color: Colors.white60, fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }
}

class _SeverityChip extends StatelessWidget {
  final String severity;
  const _SeverityChip(this.severity);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: (severityColors[severity] ?? Colors.grey).withOpacity(0.2),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: severityColors[severity] ?? Colors.grey, width: 0.5),
        ),
        child: Text(severity.toUpperCase(), style: TextStyle(color: severityColors[severity] ?? Colors.grey, fontSize: 10, fontWeight: FontWeight.bold)),
      );
}
