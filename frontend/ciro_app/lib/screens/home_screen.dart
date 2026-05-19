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

class _HomeScreenState extends State<HomeScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseCtrl;
  late final Animation<double> _pulse;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
        vsync: this, duration: const Duration(seconds: 2))
      ..repeat(reverse: true);
    _pulse = Tween(begin: 0.5, end: 1.0).animate(
        CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut));
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().checkHealth();
    });
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final outcome = state.outcomeSummary;
    final event = state.lastPipelineResult?.event;

    return Scaffold(
      backgroundColor: kBg,
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            pinned: true,
            expandedHeight: 100,
            backgroundColor: kBg,
            flexibleSpace: FlexibleSpaceBar(
              titlePadding: const EdgeInsets.only(left: 16, bottom: 14),
              title: Row(children: [
                AnimatedBuilder(
                  animation: _pulse,
                  builder: (_, __) => Opacity(
                    opacity: state.isOnline ? _pulse.value : 1.0,
                    child: Container(
                      width: 8, height: 8,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: state.isOnline ? kAccent : kDanger,
                        boxShadow: state.isOnline
                            ? [BoxShadow(color: kAccent.withOpacity(0.7), blurRadius: 8)]
                            : [],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                const Text('CIRO',
                    style: TextStyle(
                        color: kPrimary, fontSize: 22,
                        fontWeight: FontWeight.w800, letterSpacing: 2)),
                const SizedBox(width: 6),
                Text(state.isOnline ? 'LIVE' : 'OFFLINE',
                    style: TextStyle(
                        color: state.isOnline ? kAccent : kDanger,
                        fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
              ]),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft, end: Alignment.bottomRight,
                    colors: [Color(0xFF060A14), Color(0xFF0A1628)],
                  ),
                ),
              ),
            ),
            actions: [
              IconButton(
                  icon: const Icon(Icons.refresh_rounded, color: Colors.white54),
                  onPressed: () => context.read<AppState>().refreshAll()),
              IconButton(
                  icon: const Icon(Icons.restart_alt_rounded, color: Colors.white38),
                  tooltip: 'Reset',
                  onPressed: () => _confirmReset(context)),
              const SizedBox(width: 4),
            ],
          ),

          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
            sliver: SliverList(
              delegate: SliverChildListDelegate([

                // ── Command Centre ─────────────────────────────────────────
                _CommandCard(state: state, event: event),
                const SizedBox(height: 14),

                // ── Quick Stats ────────────────────────────────────────────
                _QuickStatsRow(state: state),
                const SizedBox(height: 14),

                // ── Outcome ────────────────────────────────────────────────
                _Label('RESPONSE OUTCOME'),
                const SizedBox(height: 10),
                if (outcome != null) ...[
                  _OutcomeGrid(outcome: outcome),
                  if (outcome.resourcesOpened.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    _ResourcesCard(resources: outcome.resourcesOpened),
                  ],
                ] else
                  _EmptyCard(Icons.bolt_rounded,
                      'Trigger the pipeline to see outcome metrics'),

                // ── Recent Alerts ──────────────────────────────────────────
                if (state.alerts.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  _Label('RECENT ALERTS  •  ${state.alerts.length} TOTAL'),
                  const SizedBox(height: 10),
                  ...state.alerts.reversed.take(3).map(
                        (a) => _AlertPreview(alert: a)),
                ],
              ]),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor:
            state.isPipelineRunning ? Colors.grey.shade800 : kPrimary,
        foregroundColor:
            state.isPipelineRunning ? Colors.white38 : kBg,
        elevation: 8,
        onPressed: state.isPipelineRunning
            ? null
            : () => showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (_) => const BilingualInputSheet(),
                ),
        icon: state.isPipelineRunning
            ? const SizedBox(
                width: 20, height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white38))
            : const Icon(Icons.bolt_rounded),
        label: Text(
          state.isPipelineRunning ? 'RUNNING…' : 'TRIGGER PIPELINE',
          style: const TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1),
        ),
      ),
    );
  }

  Future<void> _confirmReset(BuildContext ctx) async {
    final ok = await showDialog<bool>(
      context: ctx,
      builder: (_) => AlertDialog(
        backgroundColor: kCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Reset Simulation?',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        content: const Text(
            'This clears all alerts, tickets and pipeline state.',
            style: TextStyle(color: Colors.white60)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('CANCEL', style: TextStyle(color: Colors.white38))),
          ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: kDanger),
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('RESET')),
        ],
      ),
    );
    if (ok == true && ctx.mounted) ctx.read<AppState>().resetAll();
  }
}

// ── Command Centre Card ───────────────────────────────────────────────────────

class _CommandCard extends StatelessWidget {
  final AppState state;
  final CrisisEvent? event;
  const _CommandCard({required this.state, this.event});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF0E1A35), Color(0xFF131C30)],
            begin: Alignment.topLeft, end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: kCardBorder),
          boxShadow: [
            BoxShadow(color: kPrimary.withOpacity(0.04), blurRadius: 20, spreadRadius: 2)
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.radar_rounded, color: kPrimary, size: 18),
              const SizedBox(width: 8),
              const Text('COMMAND CENTRE',
                  style: TextStyle(
                      color: kPrimary, fontWeight: FontWeight.w800,
                      letterSpacing: 1.5, fontSize: 12)),
              const Spacer(),
              if (state.isPipelineRunning)
                const SizedBox(
                    width: 14, height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: kPrimary)),
            ]),
            const SizedBox(height: 14),
            if (event != null) ...[
              Row(children: [
                _SeverityPill(event!.severity),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '${event!.crisisType.toUpperCase()} · ${event!.location}',
                    style: const TextStyle(
                        color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
                  ),
                ),
              ]),
              const SizedBox(height: 12),
              _ConfBar(value: event!.confidence),
              const SizedBox(height: 10),
              Text(event!.explanation,
                  style: const TextStyle(color: Colors.white54, fontSize: 12, height: 1.5)),
            ] else ...[
              const Text('No crisis detected yet',
                  style: TextStyle(color: Colors.white38, fontSize: 14)),
              const SizedBox(height: 4),
              const Text('Tap TRIGGER PIPELINE below',
                  style: TextStyle(color: Colors.white24, fontSize: 12)),
            ],
            if (state.error != null) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: kDanger.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: kDanger.withOpacity(0.3)),
                ),
                child: Row(children: [
                  const Icon(Icons.error_outline_rounded, color: kDanger, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                      child: Text(state.error!,
                          style: const TextStyle(color: kDanger, fontSize: 12))),
                ]),
              ),
            ],
          ],
        ),
      );
}

// ── Quick Stats ───────────────────────────────────────────────────────────────

class _QuickStatsRow extends StatelessWidget {
  final AppState state;
  const _QuickStatsRow({required this.state});

  @override
  Widget build(BuildContext context) => Row(children: [
        _StatPill(Icons.campaign_rounded, '${state.alerts.length}', 'Alerts', kSecondary),
        const SizedBox(width: 8),
        _StatPill(Icons.assignment_rounded, '${state.tickets.length}', 'Tickets', kWarning),
        const SizedBox(width: 8),
        _StatPill(Icons.account_tree_rounded, '${state.latestTrace.length}', 'Steps',
            agentColors['plan']!),
      ]);
}

class _StatPill extends StatelessWidget {
  final IconData icon;
  final String value, label;
  final Color color;
  const _StatPill(this.icon, this.value, this.label, this.color);

  @override
  Widget build(BuildContext context) => Expanded(
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
          decoration: BoxDecoration(
            color: color.withOpacity(0.07),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: color.withOpacity(0.2)),
          ),
          child: Column(children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 6),
            Text(value,
                style: TextStyle(
                    color: color, fontSize: 22, fontWeight: FontWeight.w800)),
            Text(label,
                style: const TextStyle(
                    color: Colors.white38, fontSize: 10, letterSpacing: 0.5)),
          ]),
        ),
      );
}

// ── Outcome Grid ──────────────────────────────────────────────────────────────

class _OutcomeGrid extends StatelessWidget {
  final OutcomeSummary outcome;
  const _OutcomeGrid({required this.outcome});

  @override
  Widget build(BuildContext context) {
    final metrics = [
      ('CONGESTION\nREDUCED', '${outcome.congestionReductionPct.toStringAsFixed(1)}%', kAccent),
      ('VEHICLES\nREROUTED', '${outcome.vehiclesRerouted}', kPrimary),
      ('MIN ETA\n(MIN)', '${outcome.minEtaMinutes}', kWarning),
      ('ALERTS\nSENT', '${outcome.alertsDispatched}', kSecondary),
    ];
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 8,
      mainAxisSpacing: 8,
      childAspectRatio: 1.8,
      children: metrics
          .map((m) => _MetricTile(label: m.$1, value: m.$2, color: m.$3))
          .toList(),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final String label, value;
  final Color color;
  const _MetricTile({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.06),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: TextStyle(
                    color: color.withOpacity(0.7), fontSize: 10, letterSpacing: 0.8)),
            Text(value,
                style: TextStyle(
                    color: color, fontSize: 26, fontWeight: FontWeight.w800)),
          ],
        ),
      );
}

class _ResourcesCard extends StatelessWidget {
  final List<String> resources;
  const _ResourcesCard({required this.resources});

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: kAccent.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: kAccent.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('RESOURCES OPENED',
                style: TextStyle(
                    color: kAccent, fontSize: 10,
                    letterSpacing: 1.2, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ...resources.map((r) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(children: [
                    const Icon(Icons.check_circle_outline_rounded, color: kAccent, size: 14),
                    const SizedBox(width: 8),
                    Text(r, style: const TextStyle(color: Colors.white70, fontSize: 13)),
                  ]),
                )),
          ],
        ),
      );
}

class _AlertPreview extends StatelessWidget {
  final CiroAlert alert;
  const _AlertPreview({required this.alert});

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: kSecondary.withOpacity(0.06),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: kSecondary.withOpacity(0.2)),
        ),
        child: Row(children: [
          Icon(Icons.campaign_rounded, color: kSecondary, size: 16),
          const SizedBox(width: 10),
          Expanded(
            child: Text(alert.message,
                style: const TextStyle(color: Colors.white70, fontSize: 12),
                maxLines: 1, overflow: TextOverflow.ellipsis),
          ),
          const SizedBox(width: 8),
          Text(alert.targetArea,
              style: TextStyle(
                  color: kSecondary.withOpacity(0.8),
                  fontSize: 11, fontWeight: FontWeight.bold)),
        ]),
      );
}

// ── Small helpers ─────────────────────────────────────────────────────────────

class _Label extends StatelessWidget {
  final String text;
  const _Label(this.text);

  @override
  Widget build(BuildContext context) => Text(text,
      style: const TextStyle(
          color: Colors.white38, fontSize: 10,
          fontWeight: FontWeight.w700, letterSpacing: 1.5));
}

class _EmptyCard extends StatelessWidget {
  final IconData icon;
  final String message;
  const _EmptyCard(this.icon, this.message);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 30),
        decoration: BoxDecoration(
          color: kCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: kCardBorder),
        ),
        child: Center(
          child: Column(children: [
            Icon(icon, color: Colors.white12, size: 36),
            const SizedBox(height: 10),
            Text(message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white38, fontSize: 13)),
          ]),
        ),
      );
}

class _ConfBar extends StatelessWidget {
  final double value;
  const _ConfBar({required this.value});

  Color get _c {
    if (value >= 0.8) return kDanger;
    if (value >= 0.5) return kWarning;
    return kAccent;
  }

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('DETECTION CONFIDENCE',
                  style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1)),
              Text('${(value * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                      color: _c, fontSize: 12, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: value, minHeight: 5,
              backgroundColor: Colors.white.withOpacity(0.06),
              valueColor: AlwaysStoppedAnimation<Color>(_c),
            ),
          ),
        ],
      );
}

class _SeverityPill extends StatelessWidget {
  final String severity;
  const _SeverityPill(this.severity);

  @override
  Widget build(BuildContext context) {
    final c = severityColors[severity] ?? Colors.grey;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: c.withOpacity(0.5)),
      ),
      child: Text(severity.toUpperCase(),
          style: TextStyle(
              color: c, fontSize: 10,
              fontWeight: FontWeight.w800, letterSpacing: 1.2)),
    );
  }
}
