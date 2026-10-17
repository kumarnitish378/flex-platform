import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:maplibre_gl/maplibre_gl.dart' as maplibre;
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/supervisor_repository.dart';
import '../common/app_map.dart';

/// Supervisor live map screen (S-01).
///
/// Shows live vehicle positions and active pickup locations on a map.
class SupervisorLiveMapScreen extends ConsumerStatefulWidget {
  const SupervisorLiveMapScreen({super.key, this.isTestMode = false});

  final bool isTestMode;

  @override
  ConsumerState<SupervisorLiveMapScreen> createState() => _SupervisorLiveMapScreenState();
}

class _SupervisorLiveMapScreenState extends ConsumerState<SupervisorLiveMapScreen> {
  bool _loading = true;
  List<api.VehicleLive> _vehicles = <api.VehicleLive>[];

  @override
  void initState() {
    super.initState();
    _fetchVehicles();
  }

  Future<void> _fetchVehicles() async {
    try {
      final List<api.VehicleLive> list =
          await ref.read(supervisorRepositoryProvider).getLiveVehicles();
      if (mounted) {
        setState(() {
          _vehicles = list;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final List<MapMarker> markers = <MapMarker>[
      for (final api.VehicleLive v in _vehicles)
        if (v.position?.lat != null && v.position?.lng != null)
          MapMarker(
            id: v.id ?? 'v',
            position: maplibre.LatLng(
              v.position!.lat.toDouble(),
              v.position!.lng.toDouble(),
            ),
            title: v.registrationNo,
            color: Colors.blue,
          ),
    ];

    return Scaffold(
      key: const Key('S-01'),
      appBar: AppBar(
        title: const Text('Supervisor Map'),
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchVehicles,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : AppMap(
              key: const Key('supervisor-map'),
              isTestMode: widget.isTestMode,
              markers: markers,
            ),
    );
  }
}
