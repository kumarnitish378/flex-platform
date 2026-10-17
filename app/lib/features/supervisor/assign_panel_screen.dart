import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/supervisor_repository.dart';

/// Supervisor assign panel screen (S-03).
///
/// Shows candidate cabs list with ETA and capacity, and manual assign action.
class AssignPanelScreen extends ConsumerStatefulWidget {
  const AssignPanelScreen({required this.requestId, super.key});

  final String requestId;

  @override
  ConsumerState<AssignPanelScreen> createState() => _AssignPanelScreenState();
}

class _AssignPanelScreenState extends ConsumerState<AssignPanelScreen> {
  bool _loading = true;
  List<api.Candidate> _candidates = <api.Candidate>[];
  bool _assigning = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchCandidates();
  }

  Future<void> _fetchCandidates() async {
    try {
      final List<api.Candidate> list = await ref
          .read(supervisorRepositoryProvider)
          .getCandidates(widget.requestId);
      if (mounted) {
        setState(() {
          _candidates = list;
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

  Future<void> _confirmAssign(String vehicleId) async {
    setState(() {
      _assigning = true;
      _error = null;
    });

    try {
      await ref.read(supervisorRepositoryProvider).assignRequest(
            requestId: widget.requestId,
            vehicleId: vehicleId,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Request assigned successfully')),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _assigning = false;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('S-03'),
      appBar: AppBar(title: Text('Assign Request #${widget.requestId.length > 8 ? widget.requestId.substring(0, 8) : widget.requestId}')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    'Candidate Vehicles',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),

                  if (_error != null) ...<Widget>[
                    Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                    const SizedBox(height: 12),
                  ],

                  if (_candidates.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text('No candidate cabs available.'),
                    )
                  else
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: _candidates.length,
                      itemBuilder: (BuildContext context, int index) {
                        final api.Candidate c = _candidates[index];
                        final String vId = c.vehicleId ?? '';
                        final int etaMins = (c.etaToPickupSeconds ?? 300) ~/ 60;

                        return Card(
                          margin: const EdgeInsets.only(bottom: 12.0),
                          child: ListTile(
                            leading: const Icon(Icons.local_taxi, size: 36),
                            title: Text(c.registrationNo ?? 'Cab #$vId'),
                            subtitle: Text('ETA: $etaMins mins • Free Seats: ${c.seatsFreeAfter ?? 4}'),
                            trailing: ElevatedButton(
                              key: Key('confirm-assign-$vId'),
                              onPressed: _assigning ? null : () => _confirmAssign(vId),
                              child: const Text('Assign'),
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
