import 'package:flutter/material.dart';

/// Admin users screen (A-05).
class UsersScreen extends StatelessWidget {
  const UsersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('A-05'),
      appBar: AppBar(title: const Text('User Management')),
      body: const Center(child: Text('User Management Panel')),
    );
  }
}
