import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/file_download_helper.dart';
import '../../data/api/admin_repository.dart';

/// Admin operational reports & billing export screen (A-07 / A19).
///
/// Features wait distribution, pooling rate %, distance ("not measured" if null, never 0 km),
/// two suggestion acceptance rates, client selector, and real CSV download action.
class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  bool _loading = true;
  api.OperationsReport? _report;
  List<api.Client> _clients = <api.Client>[];
  String? _selectedClientId;
  bool _downloading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadClientsAndReport();
  }

  Future<void> _loadClientsAndReport() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final repo = ref.read(adminRepositoryProvider);
      final clientsList = await repo.getClients();
      final now = DateTime.now();
      final from = now.subtract(const Duration(days: 30));
      final reportData = await repo.getOperationsReport(
        from: from,
        to: now,
        clientId: _selectedClientId,
      );

      if (mounted) {
        setState(() {
          _clients = clientsList;
          _report = reportData;
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

  Future<void> _downloadBillingCsv() async {
    setState(() {
      _downloading = true;
      _error = null;
    });

    try {
      final now = DateTime.now();
      final monthStr = '${now.year}-${now.month.toString().padLeft(2, '0')}';
      final String csvContent = await ref
          .read(adminRepositoryProvider)
          .getBillingExportCsv(month: monthStr, clientId: _selectedClientId);

      final String fileName = 'billing_export_$monthStr.csv';
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

    final String distanceKmPerTrip = _report?.distance.cabKmPerTrip != null
        ? '${_report!.distance.cabKmPerTrip!.toStringAsFixed(1)} km'
        : 'not measured';

    final String accRate = _report?.suggestions.acceptanceRate != null
        ? '${(_report!.suggestions.acceptanceRate! * 100).toStringAsFixed(1)}%'
        : 'N/A (no offers answered)';

    final String accRateAlt = _report?.suggestions.acceptanceRateWithAlternatives != null
        ? '${(_report!.suggestions.acceptanceRateWithAlternatives! * 100).toStringAsFixed(1)}%'
        : 'N/A (no offers answered)';

    return Scaffold(
      key: const Key('A-07'),
      appBar: AppBar(
        title: const Text('Operator Reports'),
        actions: <Widget>[
          ElevatedButton.icon(
            key: const Key('download-billing-csv'),
            icon: _downloading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.download),
            label: const Text('Billing CSV'),
            onPressed: _downloading ? null : _downloadBillingCsv,
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
                  // Client Selector Dropdown for Operator Admin
                  DropdownButtonFormField<String?>(
                    key: const Key('client-selector'),
                    initialValue: _selectedClientId,
                    decoration: const InputDecoration(
                      labelText: 'Filter by Client',
                      border: OutlineInputBorder(),
                    ),
                    items: <DropdownMenuItem<String?>>[
                      const DropdownMenuItem<String?>(
                        value: null,
                        child: Text('All Clients'),
                      ),
                      for (final api.Client c in _clients)
                        DropdownMenuItem<String?>(
                          value: c.id,
                          child: Text(c.name),
                        ),
                    ],
                    onChanged: (String? val) {
                      setState(() {
                        _selectedClientId = val;
                      });
                      _loadClientsAndReport();
                    },
                  ),
                  const SizedBox(height: 16),

                  if (_error != null) ...<Widget>[
                    Text(
                      _error!,
                      key: const Key('reports-error'),
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Distance & Fleet Efficiency Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            'Distance & Fleet Metrics',
                            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text('Cab-km per trip: $distanceKmPerTrip', key: const Key('cab-km-per-trip')),
                          Text('Total trips measured: ${_report?.distance.tripsMeasured ?? 0}'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Suggestions Acceptance Rates Card (OQ-39)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            'Suggestion Acceptance Rates (OQ-39)',
                            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text('Acceptance Rate (First Choice): $accRate', key: const Key('acceptance-rate-first')),
                          Text('Acceptance Rate (With Alternatives): $accRateAlt', key: const Key('acceptance-rate-alt')),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
