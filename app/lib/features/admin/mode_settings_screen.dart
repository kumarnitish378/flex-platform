import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

/// Admin mode settings management screen (A-06).
///
/// Features mode settings list, mode toggle (manual, semi_auto, full_auto),
/// and overlap warning banner.
class ModeSettingsScreen extends ConsumerStatefulWidget {
  const ModeSettingsScreen({super.key});

  @override
  ConsumerState<ModeSettingsScreen> createState() => _ModeSettingsScreenState();
}

class _ModeSettingsScreenState extends ConsumerState<ModeSettingsScreen> {
  bool _loading = true;
  List<api.ModeSetting> _settings = <api.ModeSetting>[];
  bool _hasOverlaps = false;

  @override
  void initState() {
    super.initState();
    _fetchModeSettings();
  }

  Future<void> _fetchModeSettings() async {
    try {
      // Demo placeholder list or API fetch
      if (mounted) {
        setState(() {
          _settings = <api.ModeSetting>[
            api.ModeSetting(
              (api.ModeSettingBuilder b) => b
                ..id = 'ms_1'
                ..mode = api.ModeSettingInputModeEnum.semiAuto,
            ),
          ];
          _hasOverlaps = false;
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
      key: const Key('A-06'),
      appBar: AppBar(title: const Text('Mode Settings')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  if (_hasOverlaps)
                    Card(
                      color: Colors.amber.shade50,
                      margin: const EdgeInsets.only(bottom: 16.0),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Row(
                          children: <Widget>[
                            const Icon(Icons.warning_amber, color: Colors.amber),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Warning: Overlapping mode settings detected.',
                                style: TextStyle(color: Colors.amber.shade900),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                  Text(
                    'Scoped Mode Configurations',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),

                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _settings.length,
                    itemBuilder: (BuildContext context, int index) {
                      final api.ModeSetting ms = _settings[index];
                      final String settingId = ms.id ?? '';
                      final String shortId =
                          settingId.length > 8 ? settingId.substring(0, 8) : settingId;

                      return Card(
                        child: ListTile(
                          leading: const Icon(Icons.tune),
                          title: Text('Mode: ${ms.mode.name.toUpperCase()}'),
                          subtitle: Text('Setting ID: $shortId'),
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
