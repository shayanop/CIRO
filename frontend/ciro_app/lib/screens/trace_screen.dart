import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../theme.dart';

class TraceScreen extends StatefulWidget {
  const TraceScreen({super.key});

  @override
  State<TraceScreen> createState() => _TraceScreenState();
}

class _TraceScreenState extends State<TraceScreen> {
  final Set<int> _expanded = {};

  @override
  Widget build(BuildContext context) {
    final steps = context.watch<AppState>().latestTrace;

    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        title: const Text('Agent Trace'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => context.read<AppState>().refreshAll(),
          ),
        ],
      ),
      body: steps.isEmpty
          ? const _EmptyTrace()
          : RefreshIndicator(
              color: kPrimary,
              backgroundColor: kCard,
              onRefresh: () => context.read<AppState>().refreshAll(),
              child: CustomScrollView(
                slivers: [
                  // header summary
                  SliverToBoxAdapter(
                    child: _TraceSummaryBar(steps: steps),
                  ),
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (ctx, i) => _StepTile(
                          step: steps[i],
                          index: i,
                          isLast: i == steps.length - 1,
                          isExpanded: _expanded.contains(i),
                          onToggle: () => setState(() {
                            _expanded.contains(i)
                                ? _expanded.remove(i)
                                : _expanded.add(i);
                          }),
                        ),
                        childCount: steps.length,
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

// ── Summary Bar ───────────────────────────────────────────────────────────────

class _TraceSummaryBar extends StatelessWidget {
  final List<TraceStep> steps;
  const _TraceSummaryBar({required this.steps});

  int get _totalMs =>
      steps.fold(0, (sum, s) => sum + s.durationMs);

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.fromLTRB(16, 14, 16, 0),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: kPrimary.withOpacity(0.06),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: kPrimary.withOpacity(0.2)),
        ),
        child: Row(
          children: [
            const Icon(Icons.account_tree_rounded, color: kPrimary, size: 16),
            const SizedBox(width: 8),
            Text('${steps.length} agents · ${_totalMs}ms total',
                style: const TextStyle(
                    color: kPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w700)),
            const Spacer(),
            const Icon(Icons.touch_app_rounded, color: Colors.white38, size: 14),
            const SizedBox(width: 4),
            const Text('Tap to expand',
                style: TextStyle(color: Colors.white38, fontSize: 11)),
          ],
        ),
      );
}

// ── Step Tile ─────────────────────────────────────────────────────────────────

class _StepTile extends StatelessWidget {
  final TraceStep step;
  final int index;
  final bool isLast;
  final bool isExpanded;
  final VoidCallback onToggle;

  const _StepTile({
    required this.step,
    required this.index,
    required this.isLast,
    required this.isExpanded,
    required this.onToggle,
  });

  Color get _color {
    final a = step.agent.toLowerCase();
    if (a.contains('ingest') || a.contains('signal')) return agentColors['signal']!;
    if (a.contains('detect')) return agentColors['detect']!;
    if (a.contains('reason')) return agentColors['reason']!;
    if (a.contains('plan')) return agentColors['plan']!;
    if (a.contains('simul')) return agentColors['simulate']!;
    return Colors.grey;
  }

  String get _agentLabel {
    final a = step.agent.toLowerCase();
    if (a.contains('ingest') || a.contains('signal')) return 'Signal Ingestion';
    if (a.contains('detect')) return 'Event Detection';
    if (a.contains('reason')) return 'Reasoning & Analysis';
    if (a.contains('plan')) return 'Action Planning';
    if (a.contains('simul')) return 'Simulation Engine';
    return step.agent;
  }

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── Timeline column ──────────────────────────────────────────────
          SizedBox(
            width: 50,
            child: Column(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _color.withOpacity(0.12),
                    border: Border.all(color: _color, width: 2),
                  ),
                  child: Center(
                    child: Text(
                      '${index + 1}',
                      style: TextStyle(
                          color: _color,
                          fontWeight: FontWeight.w800,
                          fontSize: 14),
                    ),
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: Colors.white.withOpacity(0.06),
                    ),
                  ),
              ],
            ),
          ),
          // ── Card ─────────────────────────────────────────────────────────
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: isLast ? 0 : 12),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 250),
                decoration: BoxDecoration(
                  color: isExpanded ? _color.withOpacity(0.06) : kCard,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: isExpanded ? _color.withOpacity(0.4) : kCardBorder,
                  ),
                ),
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: onToggle,
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                _agentLabel,
                                style: TextStyle(
                                    color: _color,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 13),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.05),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text('${step.durationMs}ms',
                                  style: const TextStyle(
                                      color: Colors.white54, fontSize: 11)),
                            ),
                            const SizedBox(width: 8),
                            Icon(
                              isExpanded
                                  ? Icons.expand_less_rounded
                                  : Icons.expand_more_rounded,
                              color: Colors.white38,
                              size: 20,
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(step.step,
                            style: const TextStyle(
                                color: Colors.white38, fontSize: 12)),
                        if (isExpanded) ...[
                          const SizedBox(height: 14),
                          Divider(color: _color.withOpacity(0.15)),
                          const SizedBox(height: 10),
                          _JsonBlock('INPUT', step.input,
                              agentColors['signal']!),
                          const SizedBox(height: 12),
                          _JsonBlock('OUTPUT', step.output,
                              agentColors['simulate']!),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── JSON Block ────────────────────────────────────────────────────────────────

class _JsonBlock extends StatefulWidget {
  final String label;
  final Map<String, dynamic> data;
  final Color color;
  const _JsonBlock(this.label, this.data, this.color);

  @override
  State<_JsonBlock> createState() => _JsonBlockState();
}

class _JsonBlockState extends State<_JsonBlock> {
  bool _copied = false;

  @override
  Widget build(BuildContext context) {
    final pretty = const JsonEncoder.withIndent('  ').convert(widget.data);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(widget.label,
                style: TextStyle(
                    color: widget.color,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.2)),
            const Spacer(),
            GestureDetector(
              onTap: () async {
                // copy to clipboard placeholder
                setState(() => _copied = true);
                await Future.delayed(const Duration(seconds: 2));
                if (mounted) setState(() => _copied = false);
              },
              child: Row(
                children: [
                  Icon(
                    _copied ? Icons.check_rounded : Icons.copy_rounded,
                    color: _copied ? kAccent : Colors.white24,
                    size: 13,
                  ),
                  const SizedBox(width: 3),
                  Text(_copied ? 'Copied' : 'Copy',
                      style: TextStyle(
                          color: _copied ? kAccent : Colors.white24,
                          fontSize: 10)),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: widget.color.withOpacity(0.04),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: widget.color.withOpacity(0.15)),
          ),
          child: SelectableText(
            pretty,
            style: const TextStyle(
              color: Colors.white60,
              fontSize: 11,
              fontFamily: 'monospace',
              height: 1.6,
            ),
          ),
        ),
      ],
    );
  }
}

// ── Empty State ───────────────────────────────────────────────────────────────

class _EmptyTrace extends StatelessWidget {
  const _EmptyTrace();

  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.account_tree_rounded, size: 64, color: Colors.white12),
            const SizedBox(height: 16),
            const Text('No trace available',
                style: TextStyle(
                    color: Colors.white54,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            const Text('Run the pipeline from the Home tab',
                style: TextStyle(color: Colors.white24, fontSize: 13)),
          ],
        ),
      );
}
