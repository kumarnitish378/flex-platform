import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/admin_repository.dart';

/// Admin vehicles management screen (A-02).
class VehiclesScreen extends ConsumerStatefulWidget {
  const VehiclesScreen({super.key});

  @override
  ConsumerState<VehiclesScreen> createState() => _VehiclesScreenState();
}

class _VehiclesScreenState extends ConsumerState<VehiclesScreen> {
  bool _loading = true;
  List<api.Vehicle> _vehicles = <api.Vehicle>[];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    try {
      final List<api.Vehicle> list =
          await ref.read(adminRepositoryProvider).getVehicles();
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
    return Scaffold(
      key: const Key('A-02'),
      appBar: AppBar(title: const Text('Vehicles')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _vehicles.isEmpty
              ? const Center(child: Text('No vehicles registered.'))
              : ListView.builder(
                  itemCount: _vehicles.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.Vehicle v = _vehicles[index];
                    return ListTile(
                      leading: const Icon(Icons.directions_car),
                      title: Text(v.registrationNo),
                      subtitle: Text('${v.model ?? ''} • ${v.seatCapacity} seats'),
                    );
                  },
                ),
    );
  }
}
