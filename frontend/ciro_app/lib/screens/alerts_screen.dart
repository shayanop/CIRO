import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../theme.dart';

const _channelIcons = {
  'push': Icons.notifications_active_rounded,
  'sms': Icons.sms_rounded,
  'broadcast': Icons.broadcast_on_home_rounded,
  'email': Icons.email_rounded,
};

const _channelColors = {
  'push': kPrimary,
  'sms': kAccent,
  'broadcast': kWarning,
  'email': Color(0xFFA78BFA),
};

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  // track which alert/ticket ids are "new" to animate them
  final Set<String> _seenAlerts = {};
  final Set<String> _seenTickets = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().clearAlertBadge();
      context.read<AppState>().refreshAll();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        title: Row(
          children: [
            const Text('Alert Centre'),
            const SizedBox(width: 8),
            // live pulse dot
            _LiveDot(isActive: state.alerts.isNotEmpty || state.tickets.isNotEmpty),
          ],
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: kCardBorder, width: 1)),
            ),
            child: TabBar(
              controller: _tabController,
              labelColor: kPrimary,
              unselectedLabelColor: Colors.white38,
              indicatorColor: kPrimary,
              indicatorWeight: 2,
              labelStyle: const TextStyle(
                  fontWeight: FontWeight.w700, fontSize: 12, letterSpacing: 1),
              tabs: [
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.campaign_rounded, size: 16),
                      const SizedBox(width: 6),
                      const Text('ALERTS'),
                      if (state.alerts.isNotEmpty) ...[
                        const SizedBox(width: 6),
                        _CountBadge(state.alerts.length, kPrimary),
                      ],
                    ],
                  ),
                ),
                Tab(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.assignment_rounded, size: 16),
                      const SizedBox(width: 6),
                      const Text('TICKETS'),
                      if (state.tickets.isNotEmpty) ...[
                        const SizedBox(width: 6),
                        _CountBadge(state.tickets.length, kWarning),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          // polling indicator
          if (state.isOnline)
            Padding(
              padding: const EdgeInsets.only(right: 4),
              child: Tooltip(
                message: 'Auto-refreshing every 4 s',
                child: Icon(Icons.sync_rounded,
                    color: kAccent.withOpacity(0.7), size: 18),
              ),
            ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => context.read<AppState>().refreshAll(),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _AlertsTab(seenIds: _seenAlerts),
          _TicketsTab(seenIds: _seenTickets),
        ],
      ),
    );
  }
}

// ── Alerts Tab ────────────────────────────────────────────────────────────────

class _AlertsTab extends StatelessWidget {
  final Set<String> seenIds;
  const _AlertsTab({required this.seenIds});

  @override
  Widget build(BuildContext context) {
    final alerts = context.watch<AppState>().alerts;

    if (alerts.isEmpty) {
      return const _EmptyPane(
        icon: Icons.campaign_rounded,
        title: 'No alerts dispatched',
        subtitle: 'Alerts appear here in real-time\nas the pipeline runs',
      );
    }

    return RefreshIndicator(
      color: kPrimary,
      backgroundColor: kCard,
      onRefresh: () => context.read<AppState>().refreshAll(),
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 24),
        itemCount: alerts.length,
        itemBuilder: (ctx, i) {
          // reverse so newest is first
          final a = alerts[alerts.length - 1 - i];
          final isNew = !seenIds.contains(a.alertId);
          if (isNew) seenIds.add(a.alertId);
          return _AlertCard(alert: a, isNew: isNew);
        },
      ),
    );
  }
}

class _AlertCard extends StatefulWidget {
  final CiroAlert alert;
  final bool isNew;
  const _AlertCard({required this.alert, required this.isNew});

  @override
  State<_AlertCard> createState() => _AlertCardState();
}

class _AlertCardState extends State<_AlertCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _fade;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 420));
    _fade = CurvedAnimation(parent: _ctrl, curve: Curves.easeOut);
    _slide = Tween(begin: const Offset(0, 0.12), end: Offset.zero)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
    if (widget.isNew) {
      _ctrl.forward();
    } else {
      _ctrl.value = 1.0;
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final a = widget.alert;
    final color = _channelColors[a.channel] ?? kPrimary;
    final icon = _channelIcons[a.channel] ?? Icons.notifications_rounded;

    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(
        position: _slide,
        child: Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: kCard,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: widget.isNew
                  ? color.withOpacity(0.5)
                  : kCardBorder,
            ),
            boxShadow: widget.isNew
                ? [BoxShadow(color: color.withOpacity(0.12), blurRadius: 12)]
                : [],
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(icon, color: color, size: 18),
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
                                  a.targetArea,
                                  style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w700,
                                      fontSize: 14),
                                ),
                              ),
                              _ChannelChip(a.channel, color),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _formatTime(a.sentAt),
                            style: const TextStyle(
                                color: Colors.white38, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  a.message,
                  style: const TextStyle(
                      color: Colors.white70, fontSize: 13, height: 1.4),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Icon(Icons.people_rounded,
                        size: 13, color: Colors.white38),
                    const SizedBox(width: 5),
                    Text(
                      '${_formatCount(a.recipientsCount)} recipients',
                      style: const TextStyle(
                          color: Colors.white38, fontSize: 12),
                    ),
                    const Spacer(),
                    if (widget.isNew)
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 7, vertical: 2),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          'NEW',
                          style: TextStyle(
                              color: color,
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── Tickets Tab ───────────────────────────────────────────────────────────────

class _TicketsTab extends StatelessWidget {
  final Set<String> seenIds;
  const _TicketsTab({required this.seenIds});

  @override
  Widget build(BuildContext context) {
    final tickets = context.watch<AppState>().tickets;

    if (tickets.isEmpty) {
      return const _EmptyPane(
        icon: Icons.assignment_rounded,
        title: 'No tickets created',
        subtitle: 'Emergency tickets appear here\nwhen the pipeline dispatches units',
      );
    }

    return RefreshIndicator(
      color: kPrimary,
      backgroundColor: kCard,
      onRefresh: () => context.read<AppState>().refreshAll(),
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 24),
        itemCount: tickets.length,
        itemBuilder: (ctx, i) {
          final t = tickets[tickets.length - 1 - i];
          final isNew = !seenIds.contains(t.ticketId);
          if (isNew) seenIds.add(t.ticketId);
          return _TicketCard(ticket: t, isNew: isNew);
        },
      ),
    );
  }
}

class _TicketCard extends StatelessWidget {
  final EmergencyTicket ticket;
  final bool isNew;
  const _TicketCard({required this.ticket, required this.isNew});

  @override
  Widget build(BuildContext context) {
    final statusData = {
      'open': (Colors.white38, Icons.radio_button_unchecked_rounded),
      'dispatched': (kPrimary, Icons.local_shipping_rounded),
      'resolved': (kAccent, Icons.check_circle_rounded),
    };
    final (statusColor, statusIcon) =
        statusData[ticket.status] ?? (Colors.grey, Icons.help_outline_rounded);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: kCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isNew ? kWarning.withOpacity(0.5) : kCardBorder,
        ),
        boxShadow: isNew
            ? [BoxShadow(color: kWarning.withOpacity(0.1), blurRadius: 12)]
            : [],
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(statusIcon, color: statusColor, size: 18),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        ticket.unitDispatched,
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 14),
                      ),
                      Text(
                        ticket.location,
                        style: const TextStyle(
                            color: Colors.white54, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                _StatusChip(ticket.status, statusColor),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.03),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  _InfoItem(Icons.timer_rounded, 'ETA',
                      '${ticket.etaMinutes} min'),
                  const SizedBox(width: 16),
                  _InfoItem(Icons.crisis_alert_rounded, 'TYPE',
                      ticket.crisisType.toUpperCase()),
                  const Spacer(),
                  Text(_formatTime(ticket.createdAt),
                      style: const TextStyle(
                          color: Colors.white38, fontSize: 11)),
                ],
              ),
            ),
            const SizedBox(height: 10),
            _StatusButtons(ticket: ticket),
          ],
        ),
      ),
    );
  }
}

class _InfoItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _InfoItem(this.icon, this.label, this.value);

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Icon(icon, size: 12, color: Colors.white38),
          const SizedBox(width: 4),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: const TextStyle(
                      color: Colors.white24,
                      fontSize: 9,
                      letterSpacing: 0.5)),
              Text(value,
                  style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 11,
                      fontWeight: FontWeight.w600)),
            ],
          ),
        ],
      );
}

class _StatusButtons extends StatelessWidget {
  final EmergencyTicket ticket;
  const _StatusButtons({required this.ticket});

  @override
  Widget build(BuildContext context) {
    const statuses = ['open', 'dispatched', 'resolved'];
    final colors = {
      'open': Colors.white38,
      'dispatched': kPrimary,
      'resolved': kAccent,
    };

    return Row(
      children: statuses.map((s) {
        final isActive = ticket.status == s;
        final c = colors[s]!;
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 3),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(
                  foregroundColor: isActive ? c : Colors.white24,
                  backgroundColor: isActive ? c.withOpacity(0.1) : null,
                  side: BorderSide(
                      color: isActive ? c : Colors.white12, width: 1),
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8)),
                  textStyle: const TextStyle(
                      fontSize: 10, fontWeight: FontWeight.w700),
                ),
                onPressed: isActive
                    ? null
                    : () => context
                        .read<AppState>()
                        .updateTicketStatus(ticket.ticketId, s),
                child: Text(s.toUpperCase()),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

// ── Shared sub-widgets ────────────────────────────────────────────────────────

class _EmptyPane extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  const _EmptyPane(
      {required this.icon, required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 52, color: Colors.white12),
            const SizedBox(height: 16),
            Text(title,
                style: const TextStyle(
                    color: Colors.white54,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            Text(subtitle,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white24, fontSize: 13)),
          ],
        ),
      );
}

class _ChannelChip extends StatelessWidget {
  final String channel;
  final Color color;
  const _ChannelChip(this.channel, this.color);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: color.withOpacity(0.35)),
        ),
        child: Text(channel.toUpperCase(),
            style: TextStyle(
                color: color,
                fontSize: 9,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.8)),
      );
}

class _StatusChip extends StatelessWidget {
  final String status;
  final Color color;
  const _StatusChip(this.status, this.color);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: color.withOpacity(0.12),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color.withOpacity(0.35)),
        ),
        child: Text(status.toUpperCase(),
            style: TextStyle(
                color: color,
                fontSize: 9,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.8)),
      );
}

class _CountBadge extends StatelessWidget {
  final int count;
  final Color color;
  const _CountBadge(this.count, this.color);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
        decoration: BoxDecoration(
          color: color.withOpacity(0.2),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text('$count',
            style: TextStyle(
                color: color, fontSize: 10, fontWeight: FontWeight.w800)),
      );
}

class _LiveDot extends StatefulWidget {
  final bool isActive;
  const _LiveDot({required this.isActive});

  @override
  State<_LiveDot> createState() => _LiveDotState();
}

class _LiveDotState extends State<_LiveDot> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(seconds: 1))
      ..repeat(reverse: true);
    _anim = Tween(begin: 0.4, end: 1.0)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _anim,
        builder: (_, __) => Opacity(
          opacity: widget.isActive ? _anim.value : 0.3,
          child: Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: widget.isActive ? kAccent : Colors.white24,
              boxShadow: widget.isActive
                  ? [BoxShadow(color: kAccent.withOpacity(0.5), blurRadius: 5)]
                  : [],
            ),
          ),
        ),
      );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

String _formatTime(String iso) {
  try {
    final dt = DateTime.parse(iso).toLocal();
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    return '$hh:$mm';
  } catch (_) {
    return iso;
  }
}

String _formatCount(int n) {
  if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}k';
  return '$n';
}
