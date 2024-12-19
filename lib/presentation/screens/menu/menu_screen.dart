import 'package:flutter/material.dart';
import 'components/menu_form.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class MenuScreen extends StatefulWidget {
  const MenuScreen({super.key});

  @override
  State<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends State<MenuScreen> {
  bool _showForm = false;
  List<Map<String, dynamic>> categories = [];
  final supabase = Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    try {
      final response = await supabase
          .from('food_table')
          .select('food_category, food_photo, rate::float')
          .order('rate', ascending: false);

      if (mounted) {
        final categoryMap = <String, Map<String, dynamic>>{};
        for (var item in response as List) {
          final category = item['food_category'].toString();
          if (!categoryMap.containsKey(category)) {
            categoryMap[category] = item;
          }
        }

        setState(() {
          categories = categoryMap.values.toList();
        });
      }
    } catch (e) {
      print('Error loading categories: $e');
      print('Error details: ${e.toString()}');
    }
  }

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
            const SizedBox(height: 16),
            SizedBox(
              height: 200, // Ajusta la altura según necesites
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: categories.length,
                itemBuilder: (context, index) {
                  final item = categories[index];
                  final category = item['food_category'];
                  final photoUrl = item['food_photo'];
                  final rating =
                      (item['rate'] as num?)?.toStringAsFixed(1) ?? '0.0';

                  return Padding(
                    padding: const EdgeInsets.only(right: 16.0),
                    child: Container(
                      width: 200,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ClipRRect(
                            borderRadius: const BorderRadius.vertical(
                                top: Radius.circular(12)),
                            child: photoUrl != null
                                ? Image.network(
                                    photoUrl,
                                    height: 120,
                                    width: double.infinity,
                                    fit: BoxFit.cover,
                                  )
                                : Container(
                                    height: 120,
                                    color: Colors.grey[200],
                                    child: const Icon(Icons.image, size: 40),
                                  ),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  category ?? 'Sin categoría',
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    const Icon(Icons.star,
                                        size: 16, color: Colors.amber),
                                    const SizedBox(width: 4),
                                    Text(rating),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
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
        padding: const EdgeInsets.all(15.0),
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
        elevation: 1,
      ),
      icon: Icon(_showForm ? Icons.close : Icons.add),
      label: Text(_showForm ? 'Close Form' : 'Add Item'),
    );
  }
}
