import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';

enum _TileStyle { street, dark, satellite }

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

  _TileStyle _tileStyle = _TileStyle.dark;
  bool _showAffected = true;
  bool _showPrimary = true;
  bool _showAlternate = true;
  bool _showPin = true;

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
      _fitToOverlay();
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  List<LatLng> _allPoints() {
    final pts = <LatLng>[];
    final o = _overlay;
    if (o == null) return pts;
    if (o.crisisPin != null) {
      pts.add(LatLng((o.crisisPin!['lat'] as num).toDouble(), (o.crisisPin!['lng'] as num).toDouble()));
    }
    for (final p in o.affectedPolygon) {
      pts.add(LatLng((p['lat'] as num).toDouble(), (p['lng'] as num).toDouble()));
    }
    for (final r in [o.primaryRoute, o.alternateRoute]) {
      if (r == null) continue;
      final line = r['polyline'] as List? ?? [];
      for (final p in line) {
        pts.add(LatLng((p['lat'] as num).toDouble(), (p['lng'] as num).toDouble()));
      }
    }
    return pts;
  }

  void _fitToOverlay() {
    final pts = _allPoints();
    if (pts.isEmpty) return;
    if (pts.length == 1) {
      _mapController.move(pts.first, 14.0);
      return;
    }
    final bounds = LatLngBounds.fromPoints(pts);
    _mapController.fitCamera(CameraFit.bounds(
      bounds: bounds,
      padding: const EdgeInsets.all(60),
    ));
  }

  void _recenterOnPin() {
    final pin = _overlay?.crisisPin;
    if (pin == null) return;
    _mapController.move(
      LatLng((pin['lat'] as num).toDouble(), (pin['lng'] as num).toDouble()),
      15.0,
    );
  }

  void _zoom(double delta) {
    final c = _mapController.camera;
    _mapController.move(c.center, (c.zoom + delta).clamp(2.0, 19.0));
  }

  String get _tileUrl {
    switch (_tileStyle) {
      case _TileStyle.dark:
        return 'https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png';
      case _TileStyle.satellite:
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      case _TileStyle.street:
        return 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
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

    LatLng center = const LatLng(33.6844, 73.0479);
    if (crisisPin != null) {
      center = LatLng((crisisPin['lat'] as num).toDouble(), (crisisPin['lng'] as num).toDouble());
    }

    final polygonPoints = polygon
        .map((p) => LatLng((p['lat'] as num).toDouble(), (p['lng'] as num).toDouble()))
        .toList();

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
          PopupMenuButton<_TileStyle>(
            tooltip: 'Map style',
            icon: const Icon(Icons.layers),
            initialValue: _tileStyle,
            onSelected: (v) => setState(() => _tileStyle = v),
            itemBuilder: (_) => const [
              PopupMenuItem(value: _TileStyle.dark, child: Text('Dark')),
              PopupMenuItem(value: _TileStyle.street, child: Text('Street')),
              PopupMenuItem(value: _TileStyle.satellite, child: Text('Satellite')),
            ],
          ),
          if (event != null)
            IconButton(
              tooltip: 'Reload overlay',
              icon: const Icon(Icons.refresh),
              onPressed: () => _loadOverlay(event.location),
            ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: center,
              initialZoom: 13.0,
              minZoom: 2,
              maxZoom: 19,
              interactionOptions: const InteractionOptions(
                flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
              ),
            ),
            children: [
              TileLayer(
                urlTemplate: _tileUrl,
                userAgentPackageName: 'com.ciro.ciro_app',
              ),
              if (_showAffected && polygonPoints.isNotEmpty)
                PolygonLayer(polygons: [
                  Polygon(
                    points: polygonPoints,
                    color: Colors.red.withOpacity(0.25),
                    borderColor: Colors.redAccent,
                    borderStrokeWidth: 2,
                  ),
                ]),
              if (_showPrimary && primaryPolyline.isNotEmpty)
                PolylineLayer(polylines: [
                  Polyline(points: primaryPolyline, color: Colors.redAccent, strokeWidth: 3),
                ]),
              if (_showAlternate && alternatePolyline.isNotEmpty)
                PolylineLayer(polylines: [
                  Polyline(
                    points: alternatePolyline,
                    color: Colors.greenAccent,
                    strokeWidth: 3,
                    isDotted: true,
                  ),
                ]),
              if (_showPin && crisisPin != null)
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
          if (_loading) const Center(child: CircularProgressIndicator()),
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

          Positioned(
            right: 12, top: 12,
            child: _ZoomControls(
              onZoomIn: () => _zoom(1),
              onZoomOut: () => _zoom(-1),
              onFit: _overlay != null ? _fitToOverlay : null,
              onRecenter: crisisPin != null ? _recenterOnPin : null,
            ),
          ),

          Positioned(
            bottom: 24, left: 12,
            child: _Legend(
              showAffected: _showAffected,
              showPrimary: _showPrimary,
              showAlternate: _showAlternate,
              showPin: _showPin,
              hasAffected: polygonPoints.isNotEmpty,
              hasPrimary: primaryPolyline.isNotEmpty,
              hasAlternate: alternatePolyline.isNotEmpty,
              hasPin: crisisPin != null,
              onToggleAffected: () => setState(() => _showAffected = !_showAffected),
              onTogglePrimary: () => setState(() => _showPrimary = !_showPrimary),
              onToggleAlternate: () => setState(() => _showAlternate = !_showAlternate),
              onTogglePin: () => setState(() => _showPin = !_showPin),
            ),
          ),

          if (_overlay != null)
            Positioned(
              bottom: 24, right: 12,
              child: _ScaleHint(zoom: () => _mapController.camera.zoom),
            ),

          if (event == null)
            Center(
              child: Card(
                color: const Color(0xFF141929),
                child: const Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Run the pipeline to load a crisis overlay',
                      style: TextStyle(color: Colors.white60)),
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

class _ZoomControls extends StatelessWidget {
  final VoidCallback onZoomIn;
  final VoidCallback onZoomOut;
  final VoidCallback? onFit;
  final VoidCallback? onRecenter;

  const _ZoomControls({
    required this.onZoomIn,
    required this.onZoomOut,
    this.onFit,
    this.onRecenter,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xCC141929),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _btn(Icons.add, 'Zoom in', onZoomIn),
          _divider(),
          _btn(Icons.remove, 'Zoom out', onZoomOut),
          _divider(),
          _btn(Icons.center_focus_strong, 'Recenter on crisis', onRecenter),
          _divider(),
          _btn(Icons.fit_screen, 'Fit overlay', onFit),
        ],
      ),
    );
  }

  Widget _divider() => Container(height: 1, width: 36, color: Colors.white12);

  Widget _btn(IconData icon, String tip, VoidCallback? onTap) => SizedBox(
        width: 40, height: 40,
        child: IconButton(
          tooltip: tip,
          padding: EdgeInsets.zero,
          iconSize: 18,
          icon: Icon(icon, color: onTap == null ? Colors.white24 : Colors.white),
          onPressed: onTap,
        ),
      );
}

class _ScaleHint extends StatelessWidget {
  final double Function() zoom;
  const _ScaleHint({required this.zoom});

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xCC141929),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Text('z${zoom().toStringAsFixed(1)}',
              style: const TextStyle(color: Colors.white60, fontSize: 11)),
        ),
      );
}

class _Legend extends StatelessWidget {
  final bool showAffected, showPrimary, showAlternate, showPin;
  final bool hasAffected, hasPrimary, hasAlternate, hasPin;
  final VoidCallback onToggleAffected, onTogglePrimary, onToggleAlternate, onTogglePin;

  const _Legend({
    required this.showAffected,
    required this.showPrimary,
    required this.showAlternate,
    required this.showPin,
    required this.hasAffected,
    required this.hasPrimary,
    required this.hasAlternate,
    required this.hasPin,
    required this.onToggleAffected,
    required this.onTogglePrimary,
    required this.onToggleAlternate,
    required this.onTogglePin,
  });

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xCC141929),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('LAYERS',
                  style: TextStyle(color: Colors.white38, fontSize: 10, letterSpacing: 1.2)),
              const SizedBox(height: 4),
              if (hasAffected)
                _LegendToggle(
                  color: Colors.redAccent.withOpacity(0.5),
                  label: 'Affected Area',
                  active: showAffected,
                  onTap: onToggleAffected,
                ),
              if (hasPrimary)
                _LegendToggle(
                  color: Colors.redAccent,
                  label: 'Blocked Route',
                  active: showPrimary,
                  onTap: onTogglePrimary,
                ),
              if (hasAlternate)
                _LegendToggle(
                  color: Colors.greenAccent,
                  label: 'Alternate Route',
                  active: showAlternate,
                  onTap: onToggleAlternate,
                  dotted: true,
                ),
              if (hasPin)
                _LegendToggle(
                  color: Colors.redAccent,
                  label: 'Crisis Pin',
                  active: showPin,
                  onTap: onTogglePin,
                  isPin: true,
                ),
            ],
          ),
        ),
      );
}

class _LegendToggle extends StatelessWidget {
  final Color color;
  final String label;
  final bool active;
  final VoidCallback onTap;
  final bool isPin;
  final bool dotted;

  const _LegendToggle({
    required this.color,
    required this.label,
    required this.active,
    required this.onTap,
    this.isPin = false,
    this.dotted = false,
  });

  @override
  Widget build(BuildContext context) {
    final faded = active ? 1.0 : 0.35;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          children: [
            Opacity(
              opacity: faded,
              child: isPin
                  ? Icon(Icons.location_pin, color: color, size: 14)
                  : dotted
                      ? _DottedLine(color: color)
                      : Container(width: 20, height: 4, color: color),
            ),
            const SizedBox(width: 6),
            Opacity(
              opacity: faded,
              child: Text(label,
                  style: const TextStyle(color: Colors.white70, fontSize: 11)),
            ),
            const SizedBox(width: 6),
            Icon(active ? Icons.visibility : Icons.visibility_off,
                size: 12, color: Colors.white38),
          ],
        ),
      ),
    );
  }
}

class _DottedLine extends StatelessWidget {
  final Color color;
  const _DottedLine({required this.color});

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 20, height: 4,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: List.generate(
            4,
            (_) => Container(width: 3, height: 4, color: color),
          ),
        ),
      );
}
