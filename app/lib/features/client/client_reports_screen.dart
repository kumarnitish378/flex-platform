import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/file_download_helper.dart';
import '../../core/session.dart';
import '../../data/api/admin_repository.dart';

/// Client usage & billing report screen (L-04 / A19).
///
/// Features billing treatment rules display (no_show_billable, late_cancel_billable, distance_basis)
/// above quantities table and CSV export download.
class ClientReportsScreen extends ConsumerStatefulWidget {
  const ClientReportsScreen({super.key});

  @override
  ConsumerState<ClientReportsScreen> createState() => _ClientReportsScreenState();
}

class _ClientReportsScreenState extends ConsumerState<ClientReportsScreen> {
  bool _loading = true;
  api.BillingExport? _billing;
  bool _downloading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchBilling();
  }

  Future<void> _fetchBilling() async {
    try {
      final Session session = ref.read(sessionProvider);
      // For client_admin role, omit clientId so server scope applies automatically
      final String? clientId = session.activeRole == Role.clientAdmin ? null : 'client_1';

      final now = DateTime.now();
      final monthStr = '${now.year}-${now.month.toString().padLeft(2, '0')}';
      final api.BillingExport? export = await ref
          .read(adminRepositoryProvider)
          .getBillingExport(month: monthStr, clientId: clientId);
      if (mounted) {
        setState(() {
          _billing = export;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString();
        });
      }
    }
  }

  Future<void> _downloadCsv() async {
    setState(() {
      _downloading = true;
      _error = null;
    });

    try {
      final Session session = ref.read(sessionProvider);
      final String? clientId = session.activeRole == Role.clientAdmin ? null : 'client_1';
      final now = DateTime.now();
      final monthStr = '${now.year}-${now.month.toString().padLeft(2, '0')}';

      final String csvContent = await ref
          .read(adminRepositoryProvider)
          .getBillingExportCsv(month: monthStr, clientId: clientId);

      final String fileName = 'client_billing_$monthStr.csv';
      await saveAndDownloadFile(fileName, csvContent);

      if (mounted) {
        setState(() {
          _downloading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Downloaded $fileName successfully')),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _downloading = false;
          _error = e.toString();
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Download failed: $_error')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('L-04'),
      appBar: AppBar(
        title: const Text('Client Usage Reports'),
        actions: <Widget>[
          IconButton(
            key: const Key('download-client-csv'),
            icon: _downloading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.download),
            tooltip: 'Download CSV',
            onPressed: _downloading ? null : _downloadCsv,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  if (_error != null) ...<Widget>[
                    Text(
                      _error!,
                      key: const Key('client-reports-error'),
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                    const SizedBox(height: 16),
                  ],

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
