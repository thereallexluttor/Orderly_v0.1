import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../home/components/sidebar.dart';
import 'components/menu_form.dart';

class CategoryItemsScreen extends StatefulWidget {
  final String category;

  const CategoryItemsScreen({
    super.key,
    required this.category,
  });

  @override
  State<CategoryItemsScreen> createState() => _CategoryItemsScreenState();
}

class _CategoryItemsScreenState extends State<CategoryItemsScreen> {
  final supabase = Supabase.instance.client;
  List<Map<String, dynamic>> items = [];
  bool isLoading = true;
  bool _showEditForm = false;
  Map<String, dynamic>? selectedItem;

  @override
  void initState() {
    super.initState();
    _loadItems();
  }

  Future<void> _loadItems() async {
    try {
      final response = await supabase
          .from('food_table')
          .select()
          .eq('food_category', widget.category);

      if (mounted) {
        setState(() {
          items = (response as List).cast<Map<String, dynamic>>();
          isLoading = false;
        });
      }
    } catch (e) {
      print('Error loading items: $e');
      if (mounted) {
        setState(() => isLoading = false);
      }
    }
  }

  Future<void> _deleteItem(int foodId) async {
    try {
      await supabase.from('food_table').delete().eq('food_id', foodId);
      _loadItems(); // Recargar la lista
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Item deleted successfully')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error deleting item: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          Sidebar(
            selectedItem: "Menu", // Adding required parameter
            onItemSelected: (index) {
              // Handle sidebar item selection if needed
            },
          ),
          Expanded(
            child: Scaffold(
              appBar: AppBar(
                title: Text(widget.category),
                backgroundColor: Colors.white,
                elevation: 0,
              ),
              body: Row(
                children: [
                  // Lista de items
                  Expanded(
                    flex: _showEditForm ? 2 : 3,
                    child: isLoading
                        ? const Center(child: CircularProgressIndicator())
                        : GridView.builder(
                            padding: const EdgeInsets.all(16),
                            gridDelegate:
                                const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 2,
                              childAspectRatio: 1,
                              crossAxisSpacing: 16,
                              mainAxisSpacing: 16,
                            ),
                            itemCount: items.length,
                            itemBuilder: (context, index) {
                              final item = items[index];
                              return _buildItemCard(item);
                            },
                          ),
                  ),
                  // Formulario de edición
                  if (_showEditForm && selectedItem != null)
                    Expanded(
                      flex: 1,
                      child: Card(
                        margin: const EdgeInsets.all(16),
                        child: MenuForm(
                          initialData: selectedItem,
                          onClose: () {
                            setState(() {
                              _showEditForm = false;
                              selectedItem = null;
                            });
                            _loadItems(); // Recargar items después de editar
                          },
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildItemCard(Map<String, dynamic> item) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: InkWell(
        onTap: () {
          setState(() {
            selectedItem = item;
            _showEditForm = true;
          });
        },
        borderRadius: BorderRadius.circular(8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Imagen
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(8)),
              child: item['food_photo'] != null
                  ? Image.network(
                      item['food_photo'],
                      height: 50,
                      width: double.infinity,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      height: 50,
                      color: Colors.grey[200],
                      child: const Icon(Icons.image, size: 40),
                    ),
            ),
            // Información
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item['food_name'] ?? '',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '\$${(item['food_price'] ?? 0.0).toStringAsFixed(2)}',
                          style: TextStyle(
                            fontSize: 25,
                            color: Colors.green[700],
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.star,
                                size: 14, color: Colors.amber),
                            const SizedBox(width: 2),
                            Text(
                              (item['rate'] ?? 0.0).toStringAsFixed(1),
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete, size: 16),
                          onPressed: () => _showDeleteConfirmation(item),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showDeleteConfirmation(Map<String, dynamic> item) async {
    return showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Delete'),
        content: Text('Are you sure you want to delete ${item['food_name']}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _deleteItem(item['food_id']);
            },
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
