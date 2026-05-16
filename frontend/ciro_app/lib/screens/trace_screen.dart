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
      appBar: AppBar(
        title: const Text('Agent Trace'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<AppState>().refreshAll(),
          ),
        ],
      ),
      body: steps.isEmpty
          ? const Center(
              child: Text('No trace yet.\nRun the pipeline from Home.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white38)))
          : RefreshIndicator(
              onRefresh: () => context.read<AppState>().refreshAll(),
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(vertical: 12),
                itemCount: steps.length,
                itemBuilder: (ctx, i) => _StepTile(
                  step: steps[i],
                  index: i,
                  isLast: i == steps.length - 1,
                  isExpanded: _expanded.contains(i),
                  onToggle: () => setState(() {
                    if (_expanded.contains(i)) {
                      _expanded.remove(i);
                    } else {
                      _expanded.add(i);
                    }
                  }),
                ),
              ),
            ),
    );
  }
}

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

  Color get _agentColor {
    final agent = step.agent.toLowerCase();
    if (agent.contains('ingest') || agent.contains('signal')) return agentColors['signal']!;
    if (agent.contains('detect')) return agentColors['detect']!;
    if (agent.contains('reason')) return agentColors['reason']!;
    if (agent.contains('plan')) return agentColors['plan']!;
    if (agent.contains('simul')) return agentColors['simulate']!;
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline line + dot
          SizedBox(
            width: 48,
            child: Column(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _agentColor.withOpacity(0.2),
                    border: Border.all(color: _agentColor, width: 2),
                  ),
                  child: Center(
                    child: Text('${index + 1}', style: TextStyle(color: _agentColor, fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(width: 2, color: Colors.white12),
                  ),
              ],
            ),
          ),
          // Content
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(right: 16, bottom: 16),
              child: Card(
                color: const Color(0xFF1C2340),
                child: InkWell(
                  borderRadius: BorderRadius.circular(8),
                  onTap: onToggle,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(step.agent.toUpperCase(), style: TextStyle(color: _agentColor, fontWeight: FontWeight.bold, fontSize: 13)),
                            const Spacer(),
                            Text('${step.durationMs}ms', style: const TextStyle(color: Colors.white38, fontSize: 11)),
                            const SizedBox(width: 8),
                            Icon(isExpanded ? Icons.expand_less : Icons.expand_more, color: Colors.white38, size: 18),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(step.step, style: const TextStyle(color: Colors.white60, fontSize: 12)),
                        if (isExpanded) ...[
                          const SizedBox(height: 12),
                          const Divider(color: Colors.white12),
                          const SizedBox(height: 8),
                          _JsonBlock('INPUT', step.input, const Color(0xFF2196F3)),
                          const SizedBox(height: 10),
                          _JsonBlock('OUTPUT', step.output, const Color(0xFF4CAF50)),
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

class _JsonBlock extends StatelessWidget {
  final String label;
  final Map<String, dynamic> data;
  final Color color;

  const _JsonBlock(this.label, this.data, this.color);

  @override
  Widget build(BuildContext context) {
    final pretty = const JsonEncoder.withIndent('  ').convert(data);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
        const SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withOpacity(0.05),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: color.withOpacity(0.2)),
          ),
          child: SelectableText(
            pretty,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontFamily: 'monospace',
              height: 1.5,
            ),
          ),
        ),
      ],
    );
  }
}
