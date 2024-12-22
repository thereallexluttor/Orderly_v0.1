import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
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
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadCategories();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadCategories() async {
    if (_isLoading) return;

    setState(() => _isLoading = true);

    try {
      final response = await supabase
          .from('food_table')
          .select('food_category, food_photo, rate')
          .order('rate', ascending: false);

      if (mounted) {
        final categoryMap = <String, Map<String, dynamic>>{};

        for (var item in response as List) {
          final category = item['food_category'].toString();
          if (!categoryMap.containsKey(category)) {
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
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('Error loading categories: $e');
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Error al cargar categorías: ${e.toString()}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: RefreshIndicator(
        onRefresh: _loadCategories,
        child: Container(
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
                  child: CustomScrollView(
                    controller: _scrollController,
                    slivers: [
                      const SliverToBoxAdapter(
                        child: Padding(
                          padding: EdgeInsets.only(bottom: 16),
                          child: Text(
                            'Categorías',
                            style: TextStyle(
                              fontSize: 15.3,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      SliverGrid(
                        delegate: SliverChildBuilderDelegate(
                          (context, index) =>
                              _buildCategoryCard(categories[index]),
                          childCount: categories.length,
                        ),
                        gridDelegate:
                            const SliverGridDelegateWithMaxCrossAxisExtent(
                          maxCrossAxisExtent: 250,
                          childAspectRatio: 1.2,
                          crossAxisSpacing: 16,
                          mainAxisSpacing: 16,
                        ),
                      ),
                      if (selectedCategory != null)
                        SliverToBoxAdapter(
                          child: Padding(
                            padding: const EdgeInsets.only(top: 24),
                            child: SizedBox(
                              height: 900,
                              child: CategoryItemsContent(
                                category: selectedCategory!,
                                onClose: () =>
                                    setState(() => selectedCategory = null),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryCard(Map<String, dynamic> item) {
    final category = item['food_category'];
    final photoUrl = item['food_photo'];
    final itemCount = item['item_count'];

    return GestureDetector(
      onTap: () => setState(() => selectedCategory = category),
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
              child: ClipRRect(
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(12)),
                child: photoUrl != null
                    ? CachedNetworkImage(
                        imageUrl: photoUrl,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        placeholder: (context, url) => Container(
                          color: const Color.fromARGB(255, 255, 255, 255),
                          child: const Center(
                            child: CircularProgressIndicator(),
                          ),
                        ),
                        errorWidget: (context, url, error) => Container(
                          color: const Color.fromARGB(255, 255, 255, 255),
                          child: const Icon(Icons.error),
                        ),
                      )
                    : Container(
                        color: const Color.fromARGB(255, 255, 255, 255),
                        child: const Icon(Icons.image, size: 40),
                      ),
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
                      fontSize: 12.2,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(Icons.restaurant_menu,
                          size: 16, color: Colors.grey[600]),
                      const SizedBox(width: 4),
                      Text('$itemCount items'),
                    ],
                  ),
                ],
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
            Text(
              'Add New Menu Item',
              style: TextStyle(
                fontSize: 13.8,
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
