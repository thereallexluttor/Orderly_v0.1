import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../constants/menu_constants.dart';

class CategoryCard extends StatelessWidget {
  final Map<String, dynamic> category;
  final VoidCallback onTap;

  const CategoryCard({
    super.key,
    required this.category,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final photoUrl = category['food_photo'];
    final itemCount = category['item_count'];
    final categoryName = category['food_category'];

    return GestureDetector(
      onTap: onTap,
      child: Card(
        surfaceTintColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: Colors.grey[200]!),
        ),
        color: Colors.white,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _buildImage(photoUrl),
            ),
            _buildCardContent(categoryName, itemCount),
          ],
        ),
      ),
    );
  }

  Widget _buildImage(String? photoUrl) {
    return ClipRRect(
      borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
      child: photoUrl != null
          ? CachedNetworkImage(
              imageUrl: photoUrl,
              width: double.infinity,
              fit: BoxFit.cover,
              placeholder: (context, url) => _buildLoadingPlaceholder(),
              errorWidget: (context, url, error) => _buildErrorWidget(),
            )
          : _buildEmptyImage(),
    );
  }

  Widget _buildCardContent(String? categoryName, int itemCount) {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            categoryName ?? 'Sin categoría',
            style: const TextStyle(
              fontSize: MenuConstants.categoryItemSize,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Icon(Icons.restaurant_menu, size: 16, color: Colors.grey[600]),
              const SizedBox(width: 4),
              Text('$itemCount items'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingPlaceholder() => Container(
        color: const Color.fromARGB(255, 255, 255, 255),
        child: const Center(child: CircularProgressIndicator()),
      );

  Widget _buildErrorWidget() => Container(
        color: const Color.fromARGB(255, 255, 255, 255),
        child: const Icon(Icons.error),
      );

  Widget _buildEmptyImage() => Container(
        color: const Color.fromARGB(255, 255, 255, 255),
        child: const Icon(Icons.image, size: 40),
      );
}
