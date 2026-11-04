import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api/driver_trips_repository.dart';

/// Report issue screen for drivers (D-06).
///
/// Features issue type selector, note text field, and submission action.
class ReportIssueScreen extends ConsumerStatefulWidget {
  const ReportIssueScreen({super.key});

  @override
  ConsumerState<ReportIssueScreen> createState() => _ReportIssueScreenState();
}

class _ReportIssueScreenState extends ConsumerState<ReportIssueScreen> {
  String _issueType = 'breakdown';
  final TextEditingController _noteController = TextEditingController();
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  Future<void> _submitIssue() async {
    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      await ref.read(driverTripsRepositoryProvider).reportIssue(
            issueType: _issueType,
            note: _noteController.text.trim(),
          );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Issue reported successfully')),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('D-06'),
      appBar: AppBar(title: const Text('Report Issue')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              'Report Vehicle or Trip Issue',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            // Issue type selector
            DropdownButtonFormField<String>(
              key: const Key('issue-type-picker'),
              initialValue: _issueType,
              decoration: const InputDecoration(
                labelText: 'Issue Type',
                border: OutlineInputBorder(),
              ),
              items: const <DropdownMenuItem<String>>[
                DropdownMenuItem<String>(value: 'breakdown', child: Text('Vehicle Breakdown')),
                DropdownMenuItem<String>(value: 'accident', child: Text('Accident')),
                DropdownMenuItem<String>(value: 'flat_tire', child: Text('Flat Tire')),
                DropdownMenuItem<String>(value: 'traffic_delay', child: Text('Severe Traffic Delay')),
                DropdownMenuItem<String>(value: 'other', child: Text('Other Issue')),
              ],
              onChanged: (String? val) {
                if (val != null) {
                  setState(() {
                    _issueType = val;
                  });
                }
              },
            ),
            const SizedBox(height: 20),

            // Note text input
            TextField(
              key: const Key('issue-note-input'),
              controller: _noteController,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Notes / Details',
                hintText: 'Describe what happened...',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),

            if (_error != null) ...<Widget>[
              Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
              const SizedBox(height: 16),
            ],

            ElevatedButton(
              key: const Key('submit-issue'),
              onPressed: _submitting ? null : _submitIssue,
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Report Issue'),
            ),
          ],
        ),
      ),
    );
  }
}
