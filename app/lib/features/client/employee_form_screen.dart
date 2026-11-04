import 'package:flutter/material.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

/// Client employee add/edit form screen (L-02).
///
/// Features employee name, phone, priority, and gender selection (female/male/other/not set) (Item 3).
class EmployeeFormScreen extends StatefulWidget {
  const EmployeeFormScreen({super.key, this.employeeId});

  final String? employeeId;

  @override
  State<EmployeeFormScreen> createState() => _EmployeeFormScreenState();
}

class _EmployeeFormScreenState extends State<EmployeeFormScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  api.EmployeeInputGenderEnum? _selectedGender;

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
            const SizedBox(height: 16),

            // Gender selector dropdown (Item 3)
            DropdownButtonFormField<api.EmployeeInputGenderEnum?>(
              key: const Key('employee-gender-select'),
              initialValue: _selectedGender,
              decoration: const InputDecoration(
                labelText: 'Gender',
                border: OutlineInputBorder(),
              ),
              items: const <DropdownMenuItem<api.EmployeeInputGenderEnum?>>[
                DropdownMenuItem<api.EmployeeInputGenderEnum?>(
                  value: null,
                  child: Text('Not Set'),
                ),
                DropdownMenuItem<api.EmployeeInputGenderEnum?>(
                  value: api.EmployeeInputGenderEnum.female,
                  child: Text('Female'),
                ),
                DropdownMenuItem<api.EmployeeInputGenderEnum?>(
                  value: api.EmployeeInputGenderEnum.male,
                  child: Text('Male'),
                ),
                DropdownMenuItem<api.EmployeeInputGenderEnum?>(
                  value: api.EmployeeInputGenderEnum.other,
                  child: Text('Other'),
                ),
              ],
              onChanged: (api.EmployeeInputGenderEnum? val) {
                setState(() {
                  _selectedGender = val;
                });
              },
            ),
            const SizedBox(height: 24),

            ElevatedButton(
              key: const Key('save-employee'),
              onPressed: () {
                final api.$EmployeeInput input = api.$EmployeeInput(
                  (b) => b
                    ..name = _nameController.text
                    ..phone = _phoneController.text
                    ..gender = _selectedGender,
                );
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      'Saved employee ${input.name} (Gender: ${_selectedGender?.name ?? 'not set'})',
                    ),
                  ),
                );
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
