import 'package:flutter/material.dart';

/// Client employee add/edit form screen (L-02).
class EmployeeFormScreen extends StatefulWidget {
  const EmployeeFormScreen({super.key, this.employeeId});

  final String? employeeId;

  @override
  State<EmployeeFormScreen> createState() => _EmployeeFormScreenState();
}

class _EmployeeFormScreenState extends State<EmployeeFormScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('L-02'),
      appBar: AppBar(title: Text(widget.employeeId == null ? 'Add Employee' : 'Edit Employee')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextField(
              key: const Key('employee-name-input'),
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Full Name',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              key: const Key('employee-phone-input'),
              controller: _phoneController,
              decoration: const InputDecoration(
                labelText: 'Phone Number',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              key: const Key('save-employee'),
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('Save Employee'),
            ),
          ],
        ),
      ),
    );
  }
}
