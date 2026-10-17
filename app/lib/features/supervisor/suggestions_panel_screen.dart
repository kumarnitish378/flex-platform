import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/supervisor_repository.dart';

/// Supervisor suggestions & overrides panel (S-05).
///
/// Displays top scored suggestions with reasons, failsafe countdown, and one-tap
/// approval or override/reject decision actions.
class SuggestionsPanelScreen extends ConsumerStatefulWidget {
  const SuggestionsPanelScreen({required this.requestId, super.key});

  final String requestId;

  @override
  ConsumerState<SuggestionsPanelScreen> createState() => _SuggestionsPanelScreenState();
}

class _SuggestionsPanelScreenState extends ConsumerState<SuggestionsPanelScreen> {
  bool _loading = true;
  List<api.Candidate> _suggestions = <api.Candidate>[];
  int _failsafeSeconds = 60;
  Timer? _failsafeTimer;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchSuggestions();
    _startFailsafeCountdown();
  }

  @override
  void dispose() {
    _failsafeTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchSuggestions() async {
    try {
      final List<api.Candidate> list = await ref
          .read(supervisorRepositoryProvider)
          .getSuggestions(widget.requestId);
      if (mounted) {
        setState(() {
          _suggestions = list;
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

  void _startFailsafeCountdown() {
    _failsafeTimer = Timer.periodic(const Duration(seconds: 1), (Timer timer) {
      if (_failsafeSeconds > 0) {
        setState(() {
          _failsafeSeconds--;
        });
      } else {
        timer.cancel();
      }
    });
  }

  Future<void> _submitDecision(
    String suggestionId, {
    required String decision,
    String? reasonCode,
    String? note,
  }) async {
    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      await ref.read(supervisorRepositoryProvider).submitSuggestionDecision(
            suggestionId,
            decision: decision,
            reasonCode: reasonCode,
            note: note,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Suggestion $decision decision recorded')),
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

  void _showOverrideDialog(String suggestionId) {
    String selectedReason = 'traffic';
    final TextEditingController noteController = TextEditingController();

    showDialog<void>(
      context: context,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: const Text('Override Suggestion'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              DropdownButtonFormField<String>(
                initialValue: selectedReason,
                decoration: const InputDecoration(labelText: 'Reason Code'),
                items: const <DropdownMenuItem<String>>[
                  DropdownMenuItem<String>(value: 'traffic', child: Text('Traffic Delay')),
                  DropdownMenuItem<String>(value: 'driver_issue', child: Text('Driver Issue')),
                  DropdownMenuItem<String>(value: 'client_request', child: Text('Client Request')),
                  DropdownMenuItem<String>(value: 'safety', child: Text('Safety Precaution')),
                  DropdownMenuItem<String>(value: 'other', child: Text('Other')),
                ],
                onChanged: (String? val) {
                  if (val != null) {
                    selectedReason = val;
                  }
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: noteController,
                decoration: const InputDecoration(labelText: 'Notes (optional)'),
              ),
            ],
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                _submitDecision(
                  suggestionId,
                  decision: 'reject',
                  reasonCode: selectedReason,
                  note: noteController.text.trim(),
                );
              },
              child: const Text('Confirm Reject'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('S-05'),
      appBar: AppBar(title: Text('Suggestions #${widget.requestId.length > 8 ? widget.requestId.substring(0, 8) : widget.requestId}')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  // Failsafe Countdown Timer Banner
                  Card(
                    color: Colors.amber.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Row(
                        children: <Widget>[
                          const Icon(Icons.timer, color: Colors.amber),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Failsafe Auto-Assign in $_failsafeSeconds seconds',
                              key: const Key('failsafe-timer'),
                              style: theme.textTheme.titleSmall?.copyWith(
                                color: Colors.amber.shade900,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  if (_error != null) ...<Widget>[
                    Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                    const SizedBox(height: 16),
                  ],

                  Text(
                    'Top 3 Recommended Suggestions',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),

                  if (_suggestions.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text('No clean suggestions available for this request.'),
                    )
                  else
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _suggestions.length,
                      itemBuilder: (BuildContext context, int index) {
                        final api.Candidate c = _suggestions[index];
                        final String vId = c.vehicleId ?? 'v_$index';
                        final int etaMins = (c.etaToPickupSeconds ?? 300) ~/ 60;
                        final List<String> reasonsList =
                            c.reasons?.toList() ?? <String>['$etaMins min away', '${c.seatsFreeAfter ?? 4} seats free'];

                        return Card(
                          elevation: 3,
                          margin: const EdgeInsets.only(bottom: 16.0),
                          child: Padding(
                            padding: const EdgeInsets.all(16.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: <Widget>[
                                    Text(
                                      '#${index + 1} ${c.registrationNo ?? 'Cab #$vId'}',
                                      style: theme.textTheme.titleMedium
                                          ?.copyWith(fontWeight: FontWeight.bold),
                                    ),
                                    Chip(
                                      label: Text('ETA $etaMins m'),
                                      backgroundColor: theme.colorScheme.primaryContainer,
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),

                                // Reasons chips
                                Wrap(
                                  spacing: 6.0,
                                  children: <Widget>[
                                    for (final String reason in reasonsList)
                                      Chip(
                                        label: Text(reason, style: const TextStyle(fontSize: 11)),
                                        visualDensity: VisualDensity.compact,
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 16),

                                Row(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: <Widget>[
                                    OutlinedButton(
                                      key: Key('reject-suggestion-$vId'),
                                      onPressed: _submitting ? null : () => _showOverrideDialog(vId),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor: theme.colorScheme.error,
                                      ),
                                      child: const Text('Override'),
                                    ),
                                    const SizedBox(width: 12),
                                    ElevatedButton.icon(
                                      key: Key('approve-suggestion-$vId'),
                                      onPressed: _submitting
                                          ? null
                                          : () => _submitDecision(vId, decision: 'approve'),
                                      icon: const Icon(Icons.check),
                                      label: const Text('Approve'),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                ],
              ),
            ),
    );
  }
}
