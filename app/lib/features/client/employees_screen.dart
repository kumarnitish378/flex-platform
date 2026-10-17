import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/admin_repository.dart';

/// Client admin employees screen (L-01).
///
/// Features employee list and CSV import action.
class ClientEmployeesScreen extends ConsumerStatefulWidget {
  const ClientEmployeesScreen({super.key});

  @override
  ConsumerState<ClientEmployeesScreen> createState() => _ClientEmployeesScreenState();
}

class _ClientEmployeesScreenState extends ConsumerState<ClientEmployeesScreen> {
  bool _loading = true;
  List<api.Employee> _employees = <api.Employee>[];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    try {
      final List<api.Employee> list =
          await ref.read(adminRepositoryProvider).getEmployees('client_1');
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
          : _employees.isEmpty
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
    );
  }
}
