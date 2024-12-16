import 'package:flutter/material.dart';
import 'components/menu_form.dart';

class MenuScreen extends StatefulWidget {
  const MenuScreen({super.key});

  @override
  State<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends State<MenuScreen> {
  bool _showForm = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildHeader(),
            const SizedBox(height: 24),
            if (_showForm)
              Expanded(
                child: MenuForm(
                  onClose: () => setState(() => _showForm = false),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Card(
      elevation: 2,
      shadowColor: Colors.black.withOpacity(0.1),
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.grey[300]!),
      ),
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Add New Menu Item',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.normal,
              ),
            ),
            _buildToggleButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildToggleButton() {
    return ElevatedButton.icon(
      onPressed: () => setState(() => _showForm = !_showForm),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(
          horizontal: 20,
          vertical: 12,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: Colors.grey[300]!),
        ),
        elevation: 0,
      ),
      icon: Icon(_showForm ? Icons.close : Icons.add),
      label: Text(_showForm ? 'Close Form' : 'Add Item'),
    );
  }
}
