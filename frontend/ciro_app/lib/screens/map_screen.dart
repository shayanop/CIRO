import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/api_client.dart';
import '../services/app_state.dart';
import '../theme.dart';

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
      backgroundColor: kBg,
      appBar: AppBar(
        title: Text(event != null ? 'Map · ${event.location}' : 'Crisis Map'),
        actions: [
          PopupMenuButton<_TileStyle>(
            tooltip: 'Map style',
            color: kCard,
            icon: const Icon(Icons.layers_rounded),
            initialValue: _tileStyle,
            onSelected: (v) => setState(() => _tileStyle = v),
            itemBuilder: (_) => const [
              PopupMenuItem(value: _TileStyle.dark, child: Text('Dark Style', style: TextStyle(color: Colors.white70))),
              PopupMenuItem(value: _TileStyle.street, child: Text('Street View', style: TextStyle(color: Colors.white70))),
              PopupMenuItem(value: _TileStyle.satellite, child: Text('Satellite', style: TextStyle(color: Colors.white70))),
            ],
          ),
          if (event != null)
            IconButton(
              tooltip: 'Reload overlay',
              icon: const Icon(Icons.refresh_rounded),
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
                    color: kDanger.withOpacity(0.2),
                    borderColor: kDanger.withOpacity(0.8),
                    borderStrokeWidth: 2,
                  ),
                ]),
              if (_showPrimary && primaryPolyline.isNotEmpty)
                PolylineLayer(polylines: [
                  Polyline(points: primaryPolyline, color: kDanger, strokeWidth: 4),
                ]),
              if (_showAlternate && alternatePolyline.isNotEmpty)
                PolylineLayer(polylines: [
                  Polyline(
                    points: alternatePolyline,
                    color: kAccent,
                    strokeWidth: 4,
                    isDotted: true,
                  ),
                ]),
              if (_showPin && crisisPin != null)
                MarkerLayer(markers: [
                  Marker(
                    point: center,
                    width: 60,
                    height: 60,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        Container(
                          width: 40, height: 40,
                          decoration: BoxDecoration(shape: BoxShape.circle, color: kDanger.withOpacity(0.2)),
                        ),
                        const Icon(Icons.location_pin, color: kDanger, size: 36),
                      ],
                    ),
                  ),
                ]),
            ],
          ),
          if (_loading) const Center(child: CircularProgressIndicator(color: kPrimary)),
          if (_error != null)
            Positioned(
              top: 12, left: 12, right: 12,
              child: Container(
                decoration: BoxDecoration(
                  color: kDanger.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: kDanger),
                  boxShadow: [BoxShadow(color: Colors.black45, blurRadius: 10)],
                ),
                padding: const EdgeInsets.all(12),
                child: Text(_error!, style: const TextStyle(color: Colors.white, fontSize: 13)),
              ),
            ),

          Positioned(
            right: 16, top: 16,
            child: _ZoomControls(
              onZoomIn: () => _zoom(1),
              onZoomOut: () => _zoom(-1),
              onFit: _overlay != null ? _fitToOverlay : null,
              onRecenter: crisisPin != null ? _recenterOnPin : null,
            ),
          ),

          Positioned(
            bottom: 32, left: 16,
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

          if (event == null)
            Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                decoration: BoxDecoration(
                  color: kCard.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: kCardBorder),
                  boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20)],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.map_rounded, color: Colors.white24, size: 42),
                    const SizedBox(height: 12),
                    const Text('No Map Data', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 4),
                    const Text('Run the pipeline to load a crisis overlay', style: TextStyle(color: Colors.white38, fontSize: 13)),
                  ],
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: event != null
          ? FloatingActionButton.extended(
              onPressed: () => _runSimulation(context, state),
              backgroundColor: kPrimary,
              foregroundColor: kBg,
              elevation: 6,
              icon: const Icon(Icons.play_arrow_rounded),
              label: const Text('RUN SIMULATION', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1)),
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
    return Container(
      decoration: glassDecoration(),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _btn(Icons.add_rounded, 'Zoom in', onZoomIn),
          _divider(),
          _btn(Icons.remove_rounded, 'Zoom out', onZoomOut),
          _divider(),
          _btn(Icons.center_focus_strong_rounded, 'Recenter on crisis', onRecenter),
          _divider(),
          _btn(Icons.fit_screen_rounded, 'Fit overlay', onFit),
        ],
      ),
    );
  }

  Widget _divider() => Container(height: 1, width: 32, color: Colors.white12);

  Widget _btn(IconData icon, String tip, VoidCallback? onTap) => SizedBox(
        width: 44, height: 44,
        child: IconButton(
          tooltip: tip,
          padding: EdgeInsets.zero,
          iconSize: 20,
          icon: Icon(icon, color: onTap == null ? Colors.white24 : Colors.white70),
          onPressed: onTap,
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
  Widget build(BuildContext context) {
    if (!hasAffected && !hasPrimary && !hasAlternate && !hasPin) return const SizedBox.shrink();
    
    return Container(
      decoration: glassDecoration(opacity: 0.15),
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('LAYERS',
              style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
          const SizedBox(height: 8),
          if (hasAffected)
            _LegendToggle(
              color: kDanger.withOpacity(0.5),
              label: 'Affected Area',
              active: showAffected,
              onTap: onToggleAffected,
            ),
          if (hasPrimary)
            _LegendToggle(
              color: kDanger,
              label: 'Blocked Route',
              active: showPrimary,
              onTap: onTogglePrimary,
            ),
          if (hasAlternate)
            _LegendToggle(
              color: kAccent,
              label: 'Alternate Route',
              active: showAlternate,
              onTap: onToggleAlternate,
              dotted: true,
            ),
          if (hasPin)
            _LegendToggle(
              color: kDanger,
              label: 'Crisis Pin',
              active: showPin,
              onTap: onTogglePin,
              isPin: true,
            ),
        ],
      ),
    );
  }
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
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            Opacity(
              opacity: faded,
              child: isPin
                  ? Icon(Icons.location_pin, color: color, size: 16)
                  : dotted
                      ? _DottedLine(color: color)
                      : Container(width: 20, height: 4, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(2))),
            ),
            const SizedBox(width: 8),
            Opacity(
              opacity: faded,
              child: Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
            ),
            const SizedBox(width: 12),
            Icon(active ? Icons.visibility_rounded : Icons.visibility_off_rounded,
                size: 14, color: Colors.white24),
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
            (_) => Container(width: 3, height: 4, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(2))),
          ),
        ),
      );
}
