import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/admin_repository.dart';

/// Admin clients management screen (A-04).
class ClientsScreen extends ConsumerStatefulWidget {
  const ClientsScreen({super.key});

  @override
  ConsumerState<ClientsScreen> createState() => _ClientsScreenState();
}

class _ClientsScreenState extends ConsumerState<ClientsScreen> {
  bool _loading = true;
  List<api.Client> _clients = <api.Client>[];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    try {
      final List<api.Client> list =
          await ref.read(adminRepositoryProvider).getClients();
      if (mounted) {
        setState(() {
          _clients = list;
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
      key: const Key('A-04'),
      appBar: AppBar(title: const Text('Clients')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _clients.isEmpty
              ? const Center(child: Text('No client accounts registered.'))
              : ListView.builder(
                  itemCount: _clients.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.Client c = _clients[index];
                    return ListTile(
                      leading: const Icon(Icons.business),
                      title: Text(c.name),
                      subtitle: Text('Contact: ${c.contactName ?? c.contactPhone ?? 'N/A'}'),
                    );
                  },
                ),
    );
  }
}
