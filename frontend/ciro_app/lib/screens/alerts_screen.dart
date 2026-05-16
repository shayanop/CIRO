import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/app_state.dart';

const _channelIcons = {
  'push': Icons.notifications_active,
  'sms': Icons.sms,
  'broadcast': Icons.broadcast_on_home,
};

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alert Centre'),
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF00D4FF),
          unselectedLabelColor: Colors.white38,
          indicatorColor: const Color(0xFF00D4FF),
          tabs: const [
            Tab(text: 'ALERTS', icon: Icon(Icons.campaign, size: 18)),
            Tab(text: 'TICKETS', icon: Icon(Icons.assignment, size: 18)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<AppState>().refreshAll(),
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          const _AlertsTab(),
          const _TicketsTab(),
        ],
      ),
    );
  }
}

class _AlertsTab extends StatelessWidget {
  const _AlertsTab();

  @override
  Widget build(BuildContext context) {
    final alerts = context.watch<AppState>().alerts;
    if (alerts.isEmpty) {
      return const Center(child: Text('No alerts dispatched yet', style: TextStyle(color: Colors.white38)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: alerts.length,
      itemBuilder: (ctx, i) {
        final a = alerts[alerts.length - 1 - i];
        return _AlertCard(alert: a);
      },
    );
  }
}

class _AlertCard extends StatelessWidget {
  final CiroAlert alert;
  const _AlertCard({required this.alert});

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xFF1C2340),
        margin: const EdgeInsets.only(bottom: 10),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: const Color(0xFF7B2FBE).withOpacity(0.2),
                child: Icon(_channelIcons[alert.channel] ?? Icons.notifications, color: const Color(0xFF7B2FBE), size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(child: Text(alert.targetArea, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
                        _ChannelChip(alert.channel),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(alert.message, style: const TextStyle(color: Colors.white70, fontSize: 13)),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        const Icon(Icons.people, size: 12, color: Colors.white38),
                        const SizedBox(width: 4),
                        Text('${alert.recipientsCount} recipients', style: const TextStyle(color: Colors.white38, fontSize: 11)),
                        const Spacer(),
                        Text(_formatTime(alert.sentAt), style: const TextStyle(color: Colors.white38, fontSize: 11)),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
}

class _TicketsTab extends StatelessWidget {
  const _TicketsTab();

  @override
  Widget build(BuildContext context) {
    final tickets = context.watch<AppState>().tickets;
    if (tickets.isEmpty) {
      return const Center(child: Text('No tickets created yet', style: TextStyle(color: Colors.white38)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: tickets.length,
      itemBuilder: (ctx, i) {
        final t = tickets[tickets.length - 1 - i];
        return _TicketCard(ticket: t);
      },
    );
  }
}

class _TicketCard extends StatelessWidget {
  final EmergencyTicket ticket;
  const _TicketCard({required this.ticket});

  @override
  Widget build(BuildContext context) {
    final statusColors = {'open': Colors.orangeAccent, 'dispatched': Colors.blueAccent, 'resolved': Colors.greenAccent};
    final color = statusColors[ticket.status] ?? Colors.grey;

    return Card(
      color: const Color(0xFF1C2340),
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.local_police, color: Color(0xFF00D4FF), size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(ticket.unitDispatched, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
                _StatusChip(ticket.status, color),
              ],
            ),
            const SizedBox(height: 6),
            Text(ticket.location, style: const TextStyle(color: Colors.white60)),
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.timer, size: 12, color: Colors.white38),
                const SizedBox(width: 4),
                Text('ETA: ${ticket.etaMinutes} min', style: const TextStyle(color: Colors.white38, fontSize: 12)),
                const Spacer(),
                Text(_formatTime(ticket.createdAt), style: const TextStyle(color: Colors.white38, fontSize: 11)),
              ],
            ),
            const SizedBox(height: 10),
            _StatusRow(ticket: ticket),
          ],
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final EmergencyTicket ticket;
  const _StatusRow({required this.ticket});

  @override
  Widget build(BuildContext context) {
    final statuses = ['open', 'dispatched', 'resolved'];
    return Row(
      children: statuses.map((s) {
        final isActive = ticket.status == s;
        return Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 2),
            child: OutlinedButton(
              style: OutlinedButton.styleFrom(
                foregroundColor: isActive ? const Color(0xFF00D4FF) : Colors.white38,
                side: BorderSide(color: isActive ? const Color(0xFF00D4FF) : Colors.white12),
                padding: const EdgeInsets.symmetric(vertical: 4),
                textStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
              ),
              onPressed: isActive ? null : () => context.read<AppState>().updateTicketStatus(ticket.ticketId, s),
              child: Text(s.toUpperCase()),
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _ChannelChip extends StatelessWidget {
  final String channel;
  const _ChannelChip(this.channel);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: const Color(0xFF7B2FBE).withOpacity(0.2),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(channel.toUpperCase(), style: const TextStyle(color: Color(0xFF7B2FBE), fontSize: 10, fontWeight: FontWeight.bold)),
      );
}

class _StatusChip extends StatelessWidget {
  final String status;
  final Color color;
  const _StatusChip(this.status, this.color);

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.15),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: color, width: 0.5),
        ),
        child: Text(status.toUpperCase(), style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
      );
}

String _formatTime(String iso) {
  try {
    final dt = DateTime.parse(iso).toLocal();
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  } catch (_) {
    return iso;
  }
}
