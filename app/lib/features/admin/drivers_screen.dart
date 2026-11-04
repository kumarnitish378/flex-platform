import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/admin_repository.dart';

/// Admin drivers management screen (A-03).
class DriversScreen extends ConsumerStatefulWidget {
  const DriversScreen({super.key});

  @override
  ConsumerState<DriversScreen> createState() => _DriversScreenState();
}

class _DriversScreenState extends ConsumerState<DriversScreen> {
  bool _loading = true;
  List<api.Driver> _drivers = <api.Driver>[];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    try {
      final List<api.Driver> list =
          await ref.read(adminRepositoryProvider).getDrivers();
      if (mounted) {
        setState(() {
          _drivers = list;
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
      key: const Key('A-03'),
      appBar: AppBar(title: const Text('Drivers')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _drivers.isEmpty
              ? const Center(child: Text('No drivers registered.'))
              : ListView.builder(
                  itemCount: _drivers.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.Driver d = _drivers[index];
                    return ListTile(
                      leading: const Icon(Icons.badge),
                      title: Text(d.name),
                      subtitle: Text('Phone: ${d.phone}'),
                    );
                  },
                ),
    );
  }
}
