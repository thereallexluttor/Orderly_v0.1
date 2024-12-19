import 'package:flutter/material.dart';
import 'components/category_items_content.dart';
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
  String? selectedCategory;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  Future<void> _loadCategories() async {
    try {
      // First get all items with their rates
      final response = await supabase
          .from('food_table')
          .select('food_category, food_photo, rate')
          .order('rate', ascending: false);

      if (mounted) {
        final categoryMap = <String, Map<String, dynamic>>{};

        for (var item in response as List) {
          final category = item['food_category'].toString();
          if (!categoryMap.containsKey(category)) {
            // First item of each category will be the one with highest rate
            // due to our ordering
            categoryMap[category] = {
              'food_category': category,
              'food_photo': item['food_photo'],
              'item_count': 1,
            };
          } else {
            categoryMap[category]!['item_count']++;
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
      body: Container(
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
              )
            else
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const SizedBox(height: 16),
                      const Text(
                        'Categorías',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Container(
                        height: 400,
                        child: GridView.builder(
                          gridDelegate:
                              SliverGridDelegateWithMaxCrossAxisExtent(
                            maxCrossAxisExtent: 250,
                            childAspectRatio: 1.2,
                            crossAxisSpacing: 16,
                            mainAxisSpacing: 16,
                          ),
                          itemCount: categories.length,
                          itemBuilder: (context, index) {
                            final item = categories[index];
                            final category = item['food_category'];
                            final photoUrl = item['food_photo'];
                            final itemCount = item['item_count'];

                            return GestureDetector(
                              onTap: () {
                                setState(() {
                                  selectedCategory = category;
                                });
                              },
                              child: Container(
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: Colors.grey[300]!),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Expanded(
                                      child: ClipRRect(
                                        borderRadius:
                                            const BorderRadius.vertical(
                                                top: Radius.circular(12)),
                                        child: photoUrl != null
                                            ? Image.network(
                                                photoUrl,
                                                width: double.infinity,
                                                fit: BoxFit.cover,
                                              )
                                            : Container(
                                                color: Colors.grey[200],
                                                child: const Icon(Icons.image,
                                                    size: 40),
                                              ),
                                      ),
                                    ),
                                    Padding(
                                      padding: const EdgeInsets.all(12.0),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
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
                                              const Icon(Icons.restaurant_menu,
                                                  size: 16, color: Colors.grey),
                                              const SizedBox(width: 4),
                                              Text('${itemCount} items'),
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
                      if (selectedCategory != null) ...[
                        const SizedBox(height: 24),
                        Container(
                          height: 900,
                          color: Colors.white,
                          child: CategoryItemsContent(
                            category: selectedCategory!,
                            onClose: () =>
                                setState(() => selectedCategory = null),
                          ),
                        ),
                      ],
                    ],
                  ),
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
        borderRadius: BorderRadius.circular(6),
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
          borderRadius: BorderRadius.circular(6),
          side: BorderSide(color: Colors.grey[300]!),
        ),
        elevation: 1,
      ),
      icon: Icon(_showForm ? Icons.close : Icons.add),
      label: Text(_showForm ? 'Close Form' : 'Add Item'),
    );
  }
}
