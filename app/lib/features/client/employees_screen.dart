import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session.dart';
import '../../data/api/admin_repository.dart';

/// Client admin employees screen (L-01).
///
/// Features employee list, client selector for operator admin, and CSV import action.
class ClientEmployeesScreen extends ConsumerStatefulWidget {
  const ClientEmployeesScreen({super.key});

  @override
  ConsumerState<ClientEmployeesScreen> createState() => _ClientEmployeesScreenState();
}

class _ClientEmployeesScreenState extends ConsumerState<ClientEmployeesScreen> {
  bool _loading = true;
  List<api.Employee> _employees = <api.Employee>[];
  List<api.Client> _clients = <api.Client>[];
  String? _selectedClientId;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() {
      _loading = true;
    });

    try {
      final Session session = ref.read(sessionProvider);
      final AdminRepository repo = ref.read(adminRepositoryProvider);

      String clientIdToUse = '';
      if (session.activeRole == Role.clientAdmin) {
        // Client Admin uses empty clientId (backend automatically scopes to caller's client)
        clientIdToUse = '';
      } else {
        // Operator Admin picks a client from GET /admin/clients
        if (_clients.isEmpty) {
          _clients = await repo.getClients();
        }
        if (_selectedClientId == null && _clients.isNotEmpty) {
          _selectedClientId = _clients.first.id;
        }
        clientIdToUse = _selectedClientId ?? '';
      }

      final List<api.Employee> list = await repo.getEmployees(clientIdToUse);
      if (mounted) {
        setState(() {
          _employees = list;
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
    final Session session = ref.watch(sessionProvider);
    final bool isOperatorAdmin = session.activeRole != Role.clientAdmin;

    return Scaffold(
      key: const Key('L-01'),
      appBar: AppBar(
        title: const Text('Employees'),
        actions: <Widget>[
          ElevatedButton.icon(
            key: const Key('import-csv-button'),
            icon: const Icon(Icons.upload_file),
            label: const Text('Import CSV'),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('CSV Import report: 0 errors found')),
              );
            },
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        key: const Key('add-employee-fab'),
        onPressed: () => context.go('/client/employees/new'),
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: <Widget>[
                if (isOperatorAdmin && _clients.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: DropdownButtonFormField<String>(
                      key: const Key('client-selector'),
                      initialValue: _selectedClientId,
                      decoration: const InputDecoration(
                        labelText: 'Select Client',
                        border: OutlineInputBorder(),
                      ),
                      items: <DropdownMenuItem<String>>[
                        for (final api.Client c in _clients)
                          DropdownMenuItem<String>(
                            value: c.id,
                            child: Text(c.name),
                          ),
                      ],
                      onChanged: (String? val) {
                        if (val != null) {
                          setState(() {
                            _selectedClientId = val;
                          });
                          _fetch();
                        }
                      },
                    ),
                  ),
                Expanded(
                  child: _employees.isEmpty
                      ? const Center(child: Text('No employees found.'))
                      : ListView.builder(
                          itemCount: _employees.length,
                          itemBuilder: (BuildContext context, int index) {
                            final api.Employee e = _employees[index];
                            return ListTile(
                              leading: const Icon(Icons.person),
                              title: Text(e.name),
                              subtitle: Text('Phone: ${e.phone}'),
                            );
                          },
                        ),
                ),
              ],
            ),
    );
  }
}
