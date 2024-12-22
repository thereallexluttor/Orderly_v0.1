import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../controllers/menu_screen_controller.dart';
import '../constants/menu_constants.dart';

class MenuHeader extends StatelessWidget {
  const MenuHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shadowColor: Colors.black.withOpacity(0.1),
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(6),
        side: BorderSide(color: Colors.grey[300]!),
      ),
      child: Padding(
        padding: MenuConstants.cardPadding,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Add New Menu Item',
              style: TextStyle(
                fontSize: MenuConstants.headerFontSize,
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
    return Consumer<MenuScreenController>(
      builder: (context, controller, _) {
        return ElevatedButton.icon(
          onPressed: controller.toggleForm,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(
              horizontal: 20,
              vertical: 12,
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(6),
              side: BorderSide(color: Colors.grey[300]!),
            ),
            elevation: 1,
          ),
          icon: Icon(controller.showForm ? Icons.close : Icons.add),
          label: Text(controller.showForm ? 'Close Form' : 'Add Item'),
        );
      },
    );
  }
}
