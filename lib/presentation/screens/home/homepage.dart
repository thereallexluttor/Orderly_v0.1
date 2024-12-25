import 'package:flutter/material.dart';
import 'components/sidebar.dart';
import '../menu/menu_screen.dart';
import '../inventory/inventory_screen.dart';

class HomePage extends StatefulWidget {
  static const String routeName = '/home';

  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _selectedItem = 'Dashboard';

  Widget _getScreen() {
    switch (_selectedItem) {
      case 'Dashboard':
        return MenuScreen();
      case 'Menu':
        return const MenuScreen();
      case 'Staff':
        return const MenuScreen();
      case 'Inventory':
        return const InventoryScreen();
      case 'Order/Table':
        return const MenuScreen();
      case 'Reservation':
        return const MenuScreen();
      default:
        return const MenuScreen();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          Sidebar(
            selectedItem: _selectedItem,
            onItemSelected: (item) {
              setState(() {
                _selectedItem = item;
              });
            },
          ),
          Expanded(child: _getScreen()),
        ],
      ),
    );
  }
}
