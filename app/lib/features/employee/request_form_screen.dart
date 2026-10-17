import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:maplibre_gl/maplibre_gl.dart' as maplibre;
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/ride_request_repository.dart';
import '../../l10n/app_localizations.dart';
import '../common/app_map.dart';

/// Request form screen (E-02).
///
/// Features direction toggle, pin picker on map (no address search box), landmark text,
/// time selection, and urgency picker.
class RequestFormScreen extends ConsumerStatefulWidget {
  const RequestFormScreen({super.key, this.isTestMode = false});

  final bool isTestMode;

  @override
  ConsumerState<RequestFormScreen> createState() => _RequestFormScreenState();
}

class _RequestFormScreenState extends ConsumerState<RequestFormScreen> {
  api.Direction _direction = api.Direction.toOffice;
  bool _isNow = true;
  DateTime? _scheduledTime;
  maplibre.LatLng _selectedLocation = const maplibre.LatLng(28.5703, 77.3218); // NCR default
  final TextEditingController _landmarkController = TextEditingController();
  api.Urgency _urgency = api.Urgency.medium;
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _landmarkController.dispose();
    super.dispose();
  }

  Future<void> _submitRequest() async {
    setState(() {
      _submitting = true;
      _error = null;
    });

    try {
      final api.RideRequestInput input = api.RideRequestInput(
        (api.RideRequestInputBuilder b) => b
          ..direction = _direction
          ..requestedTime = _scheduledTime ?? DateTime.now().toUtc()
          ..location.replace(
            api.LatLng(
              (api.LatLngBuilder lb) => lb
                ..lat = _selectedLocation.latitude
                ..lng = _selectedLocation.longitude,
            ),
          )
          ..landmark = _landmarkController.text.trim().isNotEmpty
              ? _landmarkController.text.trim()
              : 'Map Pin'
          ..urgency = _urgency,
      );

      final api.RideRequest request =
          await ref.read(rideRequestRepositoryProvider).createRequest(input);

      if (mounted) {
        final String reqId = request.id ?? '';
        context.go('/employee/request/$reqId');
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
    final AppText text = AppText.of(context);
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('E-02'),
      appBar: AppBar(title: Text(text.navRequestCab)),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            // Direction toggle
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: SegmentedButton<api.Direction>(
                key: const Key('direction-toggle'),
                segments: const <ButtonSegment<api.Direction>>[
                  ButtonSegment<api.Direction>(
                    value: api.Direction.toOffice,
                    label: Text('To Office'),
                    icon: Icon(Icons.business),
                  ),
                  ButtonSegment<api.Direction>(
                    value: api.Direction.fromOffice,
                    label: Text('From Office'),
                    icon: Icon(Icons.home),
                  ),
                ],
                selected: <api.Direction>{_direction},
                onSelectionChanged: (Set<api.Direction> selection) {
                  setState(() {
                    _direction = selection.first;
                  });
                },
              ),
            ),

            // Map pin picker container (height 260) - NO address search box (ADR-0010 §A1)
            SizedBox(
              height: 260,
              child: AppMap(
                key: const Key('request-map'),
                enablePinPicker: true,
                isTestMode: widget.isTestMode,
                onPinMoved: (maplibre.LatLng loc) {
                  _selectedLocation = loc;
                },
              ),
            ),

            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  // Landmark free-text input
                  TextField(
                    key: const Key('landmark-input'),
                    controller: _landmarkController,
                    decoration: const InputDecoration(
                      labelText: 'Landmark / Pickup details',
                      hintText: 'e.g. Near Gate 2 / Sector 62',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.location_on_outlined),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Time Selection
                  Row(
                    children: <Widget>[
                      const Text('Time: ', style: TextStyle(fontWeight: FontWeight.bold)),
                      ChoiceChip(
                        key: const Key('time-picker-now'),
                        label: const Text('Now'),
                        selected: _isNow,
                        onSelected: (bool selected) {
                          if (selected) {
                            setState(() {
                              _isNow = true;
                              _scheduledTime = null;
                            });
                          }
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        key: const Key('time-picker-pick'),
                        label: Text(_scheduledTime == null
                            ? 'Pick time'
                            : '${_scheduledTime!.hour}:${_scheduledTime!.minute.toString().padLeft(2, '0')}'),
                        selected: !_isNow,
                        onSelected: (bool selected) async {
                          if (selected) {
                            final TimeOfDay? picked = await showTimePicker(
                              context: context,
                              initialTime: TimeOfDay.now(),
                            );
                            if (picked != null) {
                              final DateTime now = DateTime.now();
                              setState(() {
                                _isNow = false;
                                _scheduledTime = DateTime(
                                  now.year,
                                  now.month,
                                  now.day,
                                  picked.hour,
                                  picked.minute,
                                );
                              });
                            }
                          }
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Urgency Selector
                  Row(
                    children: <Widget>[
                      const Text('Urgency: ', style: TextStyle(fontWeight: FontWeight.bold)),
                      DropdownButton<api.Urgency>(
                        key: const Key('urgency-picker'),
                        value: _urgency,
                        items: const <DropdownMenuItem<api.Urgency>>[
                          DropdownMenuItem<api.Urgency>(
                              value: api.Urgency.low, child: Text('Low')),
                          DropdownMenuItem<api.Urgency>(
                              value: api.Urgency.medium, child: Text('Medium')),
                          DropdownMenuItem<api.Urgency>(
                              value: api.Urgency.high, child: Text('High')),
                        ],
                        onChanged: (api.Urgency? val) {
                          if (val != null) {
                            setState(() {
                              _urgency = val;
                            });
                          }
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  if (_error != null) ...<Widget>[
                    Text(
                      _error!,
                      key: const Key('request-error'),
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                    const SizedBox(height: 16),
                  ],

                  ElevatedButton(
                    key: const Key('submit-request'),
                    onPressed: _submitting ? null : _submitRequest,
                    child: _submitting
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Submit Request'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
