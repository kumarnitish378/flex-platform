import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:maplibre_gl/maplibre_gl.dart' as maplibre;

import '../../services/realtime_service.dart';
import '../common/app_map.dart';

/// Employee live tracking screen (E-04).
///
/// Features:
/// - Realtime cab location updates over WebSocket
/// - Stale indicator if no location ping received for > 60 seconds
/// - Vehicle details, driver name, and SOS button
class LiveTrackingScreen extends ConsumerStatefulWidget {
  const LiveTrackingScreen({
    required this.tripId,
    super.key,
    this.isTestMode = false,
  });

  final String tripId;
  final bool isTestMode;

  @override
  ConsumerState<LiveTrackingScreen> createState() => _LiveTrackingScreenState();
}

class _LiveTrackingScreenState extends ConsumerState<LiveTrackingScreen> {
  maplibre.LatLng _cabPosition = const maplibre.LatLng(28.5703, 77.3218);
  final maplibre.LatLng _pickupPosition = const maplibre.LatLng(28.5750, 77.3250);
  DateTime _lastPingTime = DateTime.now();
  bool _isStale = false;
  Timer? _staleCheckTimer;
  StreamSubscription<RealtimeEvent>? _eventSub;

  final String _vehicleNo = 'DL 01 AB 1234';
  final String _driverName = 'Rajesh Kumar';
  String _etaText = '5 mins';
  bool _sosSent = false;

  @override
  void initState() {
    super.initState();
    _subscribeRealtime();
    _startStaleChecker();
  }

  @override
  void dispose() {
    _staleCheckTimer?.cancel();
    _eventSub?.cancel();
    super.dispose();
  }

  void _subscribeRealtime() {
    final RealtimeService realtime = ref.read(realtimeServiceProvider);
    realtime.subscribe(<String>['trip.${widget.tripId}']);

    _eventSub = realtime.events.listen((RealtimeEvent event) {
      if (event.event == 'vehicle.location') {
        final double? lat = (event.data['lat'] as num?)?.toDouble();
        final double? lng = (event.data['lng'] as num?)?.toDouble();
        if (lat != null && lng != null) {
          setState(() {
            _cabPosition = maplibre.LatLng(lat, lng);
            _lastPingTime = DateTime.now();
            _isStale = false;
          });
        }
      } else if (event.event == 'stop.eta') {
        final String? eta = event.data['eta'] as String?;
        if (eta != null) {
          setState(() {
            _etaText = eta;
          });
        }
      }
    });
  }

  void _startStaleChecker() {
    _staleCheckTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (DateTime.now().difference(_lastPingTime).inSeconds > 60) {
        if (!_isStale) {
          setState(() {
            _isStale = true;
          });
        }
      }
    });
  }

  Future<void> _triggerSos() async {
    setState(() {
      _sosSent = true;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('SOS Alert sent to supervisor')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('E-04'),
      appBar: AppBar(
        title: const Text('Live Tracking'),
        actions: <Widget>[
          IconButton(
            key: const Key('sos-button'),
            icon: const Icon(Icons.sos, color: Colors.red),
            onPressed: _triggerSos,
            tooltip: 'Emergency SOS',
          ),
        ],
      ),
      body: Stack(
        children: <Widget>[
          // Map showing cab and pickup location
          AppMap(
            key: const Key('tracking-map'),
            initialPosition: _cabPosition,
            isTestMode: widget.isTestMode,
            markers: <MapMarker>[
              MapMarker(
                id: 'cab',
                position: _cabPosition,
                title: 'Cab',
                color: Colors.blue,
              ),
              MapMarker(
                id: 'pickup',
                position: _pickupPosition,
                title: 'Pickup',
                color: Colors.red,
              ),
            ],
          ),

          // Stale location indicator banner (> 60s without ping)
          if (_isStale)
            Positioned(
              top: 12,
              left: 16,
              right: 16,
              child: Material(
                key: const Key('stale-indicator'),
                elevation: 4,
                borderRadius: BorderRadius.circular(8),
                color: Colors.amber.shade800,
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                  child: Row(
                    children: <Widget>[
                      Icon(Icons.warning_amber_rounded, color: Colors.white),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Location update delayed (>60s)',
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Bottom sheet details
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Card(
              key: const Key('tracking-bottom-sheet'),
              margin: EdgeInsets.zero,
              shape: const RoundedRectangleBorder(
                borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
              ),
              elevation: 8,
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: <Widget>[
                        Text(
                          _vehicleNo,
                          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        Chip(
                          label: Text('ETA: $_etaText'),
                          backgroundColor: theme.colorScheme.primaryContainer,
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('Driver: $_driverName', style: theme.textTheme.bodyLarge),
                    if (_sosSent) ...<Widget>[
                      const SizedBox(height: 8),
                      const Text(
                        'SOS Alert Active',
                        style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
