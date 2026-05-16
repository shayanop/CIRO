import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  MapOverlay? _overlay;
  bool _loading = false;
  String? _error;
  final MapController _mapController = MapController();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final event = context.read<AppState>().lastPipelineResult?.event;
    if (event != null && _overlay == null) {
      _loadOverlay(event.location);
    }
  }

  Future<void> _loadOverlay(String location) async {
    setState(() { _loading = true; _error = null; });
    try {
      final overlay = await ApiClient.getCrisisOverlay(location);
      setState(() { _overlay = overlay; _loading = false; });
      if (overlay.crisisPin != null) {
        final lat = (overlay.crisisPin!['lat'] as num).toDouble();
        final lng = (overlay.crisisPin!['lng'] as num).toDouble();
        _mapController.move(LatLng(lat, lng), 13.0);
      }
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final event = state.lastPipelineResult?.event;

    final crisisPin = _overlay?.crisisPin;
    final polygon = _overlay?.affectedPolygon ?? [];
    final primaryRoute = _overlay?.primaryRoute;
    final alternateRoute = _overlay?.alternateRoute;

    LatLng center = const LatLng(33.6844, 73.0479); // Islamabad default
    if (crisisPin != null) {
      center = LatLng((crisisPin['lat'] as num).toDouble(), (crisisPin['lng'] as num).toDouble());
    }

    List<LatLng> polygonPoints = polygon.map((p) => LatLng((p['lat'] as num).toDouble(), (p['lng'] as num).toDouble())).toList();

    List<LatLng> primaryPolyline = [];
    List<LatLng> alternatePolyline = [];

    if (primaryRoute != null) {
      final pts = primaryRoute['polyline'] as List? ?? [];
      primaryPolyline = pts.map((p) => LatLng((p['lat'] as num).toDouble(), (p['lng'] as num).toDouble())).toList();
    }
    if (alternateRoute != null) {
      final pts = alternateRoute['polyline'] as List? ?? [];
      alternatePolyline = pts.map((p) => LatLng((p['lat'] as num).toDouble(), (p['lng'] as num).toDouble())).toList();
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(event != null ? 'Map · ${event.location}' : 'Crisis Map'),
        actions: [
          if (event != null)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () => _loadOverlay(event.location),
            ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(initialCenter: center, initialZoom: 13.0),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.ciro.ciro_app',
              ),
              if (polygonPoints.isNotEmpty)
                PolygonLayer(polygons: [
                  Polygon(
                    points: polygonPoints,
                    color: Colors.red.withOpacity(0.25),
                    borderColor: Colors.redAccent,
                    borderStrokeWidth: 2,
                  ),
                ]),
              if (primaryPolyline.isNotEmpty)
                PolylineLayer(polylines: [
                  Polyline(points: primaryPolyline, color: Colors.redAccent, strokeWidth: 3),
                ]),
              if (alternatePolyline.isNotEmpty)
                PolylineLayer(polylines: [
                  Polyline(points: alternatePolyline, color: Colors.greenAccent, strokeWidth: 3, isDotted: true),
                ]),
              if (crisisPin != null)
                MarkerLayer(markers: [
                  Marker(
                    point: center,
                    width: 40,
                    height: 40,
                    child: const Icon(Icons.location_pin, color: Colors.redAccent, size: 40),
                  ),
                ]),
            ],
          ),
          if (_loading)
            const Center(child: CircularProgressIndicator()),
          if (_error != null)
            Positioned(
              top: 8, left: 8, right: 8,
              child: Card(
                color: Colors.red.shade900,
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text(_error!, style: const TextStyle(color: Colors.white, fontSize: 12)),
                ),
              ),
            ),
          // Legend
          Positioned(
            bottom: 24, left: 12,
            child: _Legend(
              hasPrimary: primaryPolyline.isNotEmpty,
              hasAlternate: alternatePolyline.isNotEmpty,
              hasPolygon: polygonPoints.isNotEmpty,
            ),
          ),
          if (event == null)
            Center(
              child: Card(
                color: const Color(0xFF141929),
                child: const Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Run the pipeline to load a crisis overlay', style: TextStyle(color: Colors.white60)),
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: event != null
          ? FloatingActionButton.extended(
              onPressed: () => _runSimulation(context, state),
              backgroundColor: const Color(0xFF00D4FF),
              foregroundColor: const Color(0xFF0A0E1A),
              icon: const Icon(Icons.play_arrow),
              label: const Text('RUN SIMULATION'),
            )
          : null,
    );
  }

  Future<void> _runSimulation(BuildContext context, AppState state) async {
    final result = await state.runPipeline(
      RawSignalInput(source: 'social', text: state.lastPipelineResult!.event.explanation),
    );
    if (result != null && mounted) {
      _loadOverlay(result.event.location);
    }
  }
}

class _Legend extends StatelessWidget {
  final bool hasPrimary;
  final bool hasAlternate;
  final bool hasPolygon;

  const _Legend({required this.hasPrimary, required this.hasAlternate, required this.hasPolygon});

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xCC141929),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (hasPolygon) _LegendItem(color: Colors.redAccent.withOpacity(0.5), label: 'Affected Area'),
              if (hasPrimary) _LegendItem(color: Colors.redAccent, label: 'Blocked Route'),
              if (hasAlternate) _LegendItem(color: Colors.greenAccent, label: 'Alternate Route'),
              _LegendItem(color: Colors.redAccent, label: 'Crisis Pin', isPin: true),
            ],
          ),
        ),
      );
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;
  final bool isPin;

  const _LegendItem({required this.color, required this.label, this.isPin = false});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Row(
          children: [
            isPin
                ? Icon(Icons.location_pin, color: color, size: 14)
                : Container(width: 20, height: 4, color: color),
            const SizedBox(width: 6),
            Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
          ],
        ),
      );
}
