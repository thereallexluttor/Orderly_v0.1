import 'package:flutter/material.dart';
import '../widgets/sidebar_button.dart';

class Sidebar extends StatelessWidget {
  final String selectedItem;
  final Function(String) onItemSelected;

  const Sidebar({
    super.key,
    required this.selectedItem,
    required this.onItemSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 67,
      decoration: const BoxDecoration(
        color: Colors.black87,
        borderRadius: BorderRadius.only(
          topRight: Radius.circular(13),
          bottomRight: Radius.circular(13),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 8,
            spreadRadius: 2,
            offset: Offset(1, 0),
          ),
        ],
      ),
      child: Column(
        children: [
          const SizedBox(height: 63),
          _buildNavigationButtons(),
          const Spacer(),
          SidebarButton(
            icon: Icons.logout,
            label: 'Logout',
            onTap: () {},
            isSelected: false,
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildNavigationButtons() {
    final navigationItems = [
      ('Dashboard', 'lib/assets/icons/dashboard.png'),
      ('Menu', 'lib/assets/icons/menu.png'),
      ('Staff', 'lib/assets/icons/staff.png'),
      ('Inventory', 'lib/assets/icons/inventory.png'),
      ('Order/Table', 'lib/assets/icons/table.png'),
      ('Reservation', 'lib/assets/icons/reservation.png'),
    ];

    return Column(
      children: navigationItems
          .map((item) => SidebarButton(
                imagePath: item.$2,
                label: item.$1,
                onTap: () => onItemSelected(item.$1),
                isSelected: selectedItem == item.$1,
              ))
          .toList(),
    );
  }
}
