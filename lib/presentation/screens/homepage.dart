import 'package:flutter/material.dart';

class HomePage extends StatelessWidget {
  static const String routeName = '/home';

  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Container(
            width: 70,
            color: Colors.black87,
            child: Column(
              children: [
                const SizedBox(height: 20),
                // Logo
                Image.asset(
                  'lib/assets/logos/logo_colored_white.png',
                  width: 50,
                  height: 50,
                ),
                const SizedBox(height: 10),
                const SizedBox(height: 20),
                // Dashboard button
                _SidebarButton(
                  icon: Icons.dashboard,
                  label: 'Dashboard',
                  onTap: () {},
                ),
                _SidebarButton(
                  icon: Icons.menu_book,
                  label: 'Menu',
                  onTap: () {},
                ),
                _SidebarButton(
                  icon: Icons.people,
                  label: 'Staff',
                  onTap: () {},
                ),
                _SidebarButton(
                  icon: Icons.inventory,
                  label: 'Inventory',
                  onTap: () {},
                ),
                _SidebarButton(
                  icon: Icons.table_bar,
                  label: 'Order/Table',
                  onTap: () {},
                ),
                const Spacer(),
                // Logout button at bottom
                _SidebarButton(
                  icon: Icons.logout,
                  label: 'Logout',
                  onTap: () {},
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
          // Main content
          const Expanded(
            child: Center(
              child: Text('Welcome to HomePage!'),
            ),
          ),
        ],
      ),
    );
  }
}

// Widget auxiliar para los botones de la barra lateral
class _SidebarButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _SidebarButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        children: [
          IconButton(
            icon: Icon(icon, color: Colors.white),
            onPressed: onTap,
          ),
          Text(
            label,
            style: const TextStyle(color: Colors.white, fontSize: 10),
          ),
        ],
      ),
    );
  }
}
