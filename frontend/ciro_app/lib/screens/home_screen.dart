import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme.dart';
import '../widgets/bilingual_input.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().checkHealth();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final outcome = state.outcomeSummary;
    final event = state.lastPipelineResult?.event;

    return Scaffold(
      appBar: AppBar(
        title: const Text('CIRO'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 5,
                  backgroundColor: state.isOnline ? Colors.greenAccent : Colors.red,
                ),
                const SizedBox(width: 6),
                Text(
                  state.isOnline ? 'ONLINE' : 'OFFLINE',
                  style: TextStyle(
                    fontSize: 11,
                    color: state.isOnline ? Colors.greenAccent : Colors.red,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => context.read<AppState>().refreshAll(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Status card
            _StatusCard(state: state, event: event),
            const SizedBox(height: 16),

            // Before / After cards
            if (outcome != null) ...[
              const Text(
                'OUTCOME METRICS',
                style: TextStyle(
                  color: Colors.white38,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(child: _MetricCard('CONGESTION\nREDUCED', '${outcome.congestionReductionPct.toStringAsFixed(1)}%', Colors.greenAccent)),
                  const SizedBox(width: 8),
                  Expanded(child: _MetricCard('VEHICLES\nREROUTED', '${outcome.vehiclesRerouted}', const Color(0xFF00D4FF))),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(child: _MetricCard('MIN ETA\n(MIN)', '${outcome.minEtaMinutes}', Colors.orangeAccent)),
                  const SizedBox(width: 8),
                  Expanded(child: _MetricCard('ALERTS\nSENT', '${outcome.alertsDispatched}', Colors.purpleAccent)),
                ],
              ),
              const SizedBox(height: 8),
              _MetricCard('TICKETS\nCREATED', '${outcome.ticketsCreated}', Colors.pinkAccent),
              if (outcome.resourcesOpened.isNotEmpty) ...[
                const SizedBox(height: 8),
                Card(
                  color: const Color(0xFF1C2340),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('RESOURCES OPENED', style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
                        const SizedBox(height: 6),
                        ...outcome.resourcesOpened.map((r) => Text('• $r', style: const TextStyle(color: Colors.white70, fontSize: 13))),
                      ],
                    ),
                  ),
                ),
              ],
            ] else
              const _NoDataCard('Run the pipeline to see outcome metrics'),

            const SizedBox(height: 80),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: state.isPipelineRunning ? Colors.grey : const Color(0xFF00D4FF),
        foregroundColor: const Color(0xFF0A0E1A),
        onPressed: state.isPipelineRunning
            ? null
            : () => showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (_) => const BilingualInputSheet(),
                ),
        icon: state.isPipelineRunning
            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.bolt),
        label: Text(state.isPipelineRunning ? 'RUNNING...' : 'TRIGGER PIPELINE'),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  final AppState state;
  final CrisisEvent? event;

  const _StatusCard({required this.state, this.event});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFF1C2340),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.radar, color: Color(0xFF00D4FF), size: 20),
                const SizedBox(width: 8),
                const Text('COMMAND CENTRE', style: TextStyle(color: Color(0xFF00D4FF), fontWeight: FontWeight.bold, letterSpacing: 1)),
                const Spacer(),
                if (state.isPipelineRunning)
                  const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
              ],
            ),
            const SizedBox(height: 12),
            if (event != null) ...[
              Row(
                children: [
                  _SeverityDot(event!.severity),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${event!.crisisType.toUpperCase()} · ${event!.location}',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              _ConfidenceBar(event!.confidence),
              const SizedBox(height: 6),
              Text(event!.explanation, style: const TextStyle(color: Colors.white60, fontSize: 12)),
            ] else
              const Text('No crisis detected yet', style: TextStyle(color: Colors.white38)),
            if (state.error != null) ...[
              const SizedBox(height: 8),
              Text(state.error!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
            ],
          ],
        ),
      ),
    );
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double value;
  const _ConfidenceBar(this.value);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Text('CONFIDENCE ', style: TextStyle(color: Colors.white38, fontSize: 11)),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: value,
              backgroundColor: Colors.white12,
              valueColor: AlwaysStoppedAnimation<Color>(
                value >= 0.8 ? Colors.redAccent : value >= 0.5 ? Colors.orangeAccent : Colors.greenAccent,
              ),
            ),
          ),
        ),
        const SizedBox(width: 6),
        Text('${(value * 100).toStringAsFixed(0)}%', style: const TextStyle(color: Colors.white70, fontSize: 11)),
      ],
    );
  }
}

class _SeverityDot extends StatelessWidget {
  final String severity;
  const _SeverityDot(this.severity);

  @override
  Widget build(BuildContext context) => CircleAvatar(
        radius: 5,
        backgroundColor: severityColors[severity] ?? Colors.grey,
      );
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _MetricCard(this.label, this.value, this.color);

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xFF1C2340),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
              const SizedBox(height: 6),
              Text(value, style: TextStyle(color: color, fontSize: 28, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      );
}

class _NoDataCard extends StatelessWidget {
  final String msg;
  const _NoDataCard(this.msg);

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xFF1C2340),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(child: Text(msg, style: const TextStyle(color: Colors.white38))),
        ),
      );
}
