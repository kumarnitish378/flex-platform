import 'package:flutter/material.dart';

/// Saved places screen (E-07).
///
/// Shows saved places (Home, Office).
class SavedPlacesScreen extends StatelessWidget {
  const SavedPlacesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('E-07'),
      appBar: AppBar(title: const Text('Saved Places')),
      body: ListView(
        key: const Key('saved-places-list'),
        children: const <Widget>[
          ListTile(
            leading: Icon(Icons.home),
            title: Text('Home'),
            subtitle: Text('Sector 62, Noida'),
          ),
          ListTile(
            leading: Icon(Icons.business),
            title: Text('Office'),
            subtitle: Text('Main HQ, Sector 18'),
          ),
        ],
      ),
    );
  }
}
