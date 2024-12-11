import 'package:flutter/material.dart';

class HomePage extends StatefulWidget {
  static const String routeName = '/home';

  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _selectedItem = 'Dashboard';

  Widget _getSelectedScreen() {
    switch (_selectedItem) {
      case 'Dashboard':
        return const Center(child: Text('Dashboard Screen'));
      case 'Menu':
        return const Center(child: Text('Menu Screen'));
      case 'Staff':
        return const Center(child: Text('Staff Screen'));
      case 'Inventory':
        return const Center(child: Text('Inventory Screen'));
      case 'Order/Table':
        return const Center(child: Text('Order/Table Screen'));
      case 'Reservation':
        return const Center(child: Text('Reservation Screen'));
      default:
        return const Center(child: Text('Welcome to HomePage!'));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          Container(
            width: 70,
            decoration: const BoxDecoration(
              color: Colors.black87,
              borderRadius: BorderRadius.only(
                topRight: Radius.circular(8),
                bottomRight: Radius.circular(8),
              ),
            ),
            child: Column(
              children: [
                const SizedBox(height: 20),
                Image.asset(
                  'lib/assets/logos/logo_colored_white.png',
                  width: 50,
                  height: 50,
                ),
                const SizedBox(height: 10),
                const SizedBox(height: 20),
                _SidebarButton(
                  imagePath: 'lib/assets/icons/dashboard.png',
                  label: 'Dashboard',
                  onTap: () => setState(() => _selectedItem = 'Dashboard'),
                  isSelected: _selectedItem == 'Dashboard',
                ),
                _SidebarButton(
                  imagePath: 'lib/assets/icons/menu.png',
                  label: 'Menu',
                  onTap: () => setState(() => _selectedItem = 'Menu'),
                  isSelected: _selectedItem == 'Menu',
                ),
                _SidebarButton(
                  imagePath: 'lib/assets/icons/staff.png',
                  label: 'Staff',
                  onTap: () => setState(() => _selectedItem = 'Staff'),
                  isSelected: _selectedItem == 'Staff',
                ),
                _SidebarButton(
                  imagePath: 'lib/assets/icons/inventory.png',
                  label: 'Inventory',
                  onTap: () => setState(() => _selectedItem = 'Inventory'),
                  isSelected: _selectedItem == 'Inventory',
                ),
                _SidebarButton(
                  imagePath: 'lib/assets/icons/table.png',
                  label: 'Order/Table',
                  onTap: () => setState(() => _selectedItem = 'Order/Table'),
                  isSelected: _selectedItem == 'Order/Table',
                ),
                _SidebarButton(
                  imagePath: 'lib/assets/icons/reservation.png',
                  label: 'Reservation',
                  onTap: () => setState(() => _selectedItem = 'Reservation'),
                  isSelected: _selectedItem == 'Reservation',
                ),
                const Spacer(),
                _SidebarButton(
                  icon: Icons.logout,
                  label: 'Logout',
                  onTap: () {},
                  isSelected: false,
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
          Expanded(
            child: _getSelectedScreen(),
          ),
        ],
      ),
    );
  }
}

class _SidebarButton extends StatelessWidget {
  final IconData? icon;
  final String? imagePath;
  final String label;
  final VoidCallback onTap;
  final bool isSelected;

  const _SidebarButton({
    this.icon,
    this.imagePath,
    required this.label,
    required this.onTap,
    this.isSelected = false,
  }) : assert(icon != null || imagePath != null);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        children: [
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              color: isSelected
                  ? Colors.white.withOpacity(0.2)
                  : Colors.transparent,
            ),
            child: IconButton(
              icon: imagePath != null
                  ? Image.asset(
                      imagePath!,
                      width: 24,
                      height: 24,
                    )
                  : Icon(
                      icon,
                      color: isSelected
                          ? Colors.white
                          : Colors.white.withOpacity(0.3),
                    ),
              onPressed: onTap,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              color: isSelected ? Colors.white : Colors.white.withOpacity(0.7),
              fontSize: 10,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
  }
}
