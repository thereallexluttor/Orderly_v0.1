import 'package:flutter/material.dart';

class SidebarButton extends StatelessWidget {
  final IconData? icon;
  final String? imagePath;
  final String label;
  final VoidCallback onTap;
  final bool isSelected;

  const SidebarButton({
    super.key,
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
