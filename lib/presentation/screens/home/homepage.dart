import 'package:flutter/material.dart';
import 'components/sidebar.dart';
import '../menu/menu_screen.dart';

class HomePage extends StatefulWidget {
  static const String routeName = '/home';

  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _selectedItem = 'Dashboard';

  void _handleItemSelected(String item) {
    setState(() => _selectedItem = item);
  }

  Widget _getSelectedScreen() {
    switch (_selectedItem) {
      case 'Menu':
        return const MenuScreen();
      default:
        return Center(child: Text('$_selectedItem Screen'));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          Sidebar(
            selectedItem: _selectedItem,
            onItemSelected: _handleItemSelected,
          ),
          Expanded(
            child: _getSelectedScreen(),
          ),
        ],
      ),
    );
  }
}
