import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/admin_repository.dart';

/// Client usage & billing report screen (L-04 / A19).
///
/// Features billing treatment rules display (no_show_billable, late_cancel_billable, distance_basis)
/// above quantities table.
class ClientReportsScreen extends ConsumerStatefulWidget {
  const ClientReportsScreen({super.key});

  @override
  ConsumerState<ClientReportsScreen> createState() => _ClientReportsScreenState();
}

class _ClientReportsScreenState extends ConsumerState<ClientReportsScreen> {
  bool _loading = true;
  api.BillingExport? _billing;

  @override
  void initState() {
    super.initState();
    _fetchBilling();
  }

  Future<void> _fetchBilling() async {
    try {
      final now = DateTime.now();
      final monthStr = '${now.year}-${now.month.toString().padLeft(2, '0')}';
      final api.BillingExport? export = await ref
          .read(adminRepositoryProvider)
          .getBillingExport(month: monthStr, clientId: 'client_1');
      if (mounted) {
        setState(() {
          _billing = export;
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
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('L-04'),
      appBar: AppBar(title: const Text('Client Usage Reports')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  // Billing Treatment Rules Banner
                  Card(
                    key: const Key('billing-treatment-card'),
                    color: theme.colorScheme.secondaryContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            'Billing Rules & Treatment',
                            style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text('• No-show billable: ${_billing?.treatment.noShowBillable ?? true}'),
                          Text('• Late-cancel billable: ${_billing?.treatment.lateCancelBillable ?? false}'),
                          Text('• Distance basis: ${_billing?.treatment.distanceBasis ?? 'trip_share'}'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  Text(
                    'Monthly Ride Quantities',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  ListTile(
                    title: const Text('Total Billable Rides'),
                    trailing: Text('${_billing?.summary.billableRides ?? 0}'),
                  ),
                  ListTile(
                    title: const Text('Total Distance'),
                    trailing: Text('${_billing?.summary.billableKm ?? 0} km'),
                  ),
                ],
              ),
            ),
    );
  }
}
