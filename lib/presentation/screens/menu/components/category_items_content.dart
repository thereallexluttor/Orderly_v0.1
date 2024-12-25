import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'menu_form.dart';
import 'package:provider/provider.dart';
import '../controllers/menu_screen_controller.dart';

class CategoryItemsContent extends StatefulWidget {
  final String category;
  final VoidCallback onClose;

  const CategoryItemsContent({
    super.key,
    required this.category,
    required this.onClose,
  });

  @override
  State<CategoryItemsContent> createState() => _CategoryItemsContentState();
}

class _CategoryItemsContentState extends State<CategoryItemsContent> {
  final supabase = Supabase.instance.client;
  List<Map<String, dynamic>> items = [];
  bool isLoading = true;
  bool _showEditForm = false;
  Map<String, dynamic>? selectedItem;
  bool _isGridVisible = false;

  @override
  void initState() {
    super.initState();
    _loadItems();
  }

  @override
  void didUpdateWidget(CategoryItemsContent oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.category != widget.category) {
      setState(() {
        selectedItem = null;
        _showEditForm = false;
      });
      _loadItems();
    }
  }

  Future<void> _loadItems() async {
    if (!mounted) return;

    setState(() {
      isLoading = true;
      _isGridVisible = false;
    });

    try {
      final response = await supabase
          .from('food_table')
          .select()
          .eq('food_category', widget.category);

      if (!mounted) return;

      setState(() {
        items = (response as List).cast<Map<String, dynamic>>();
        isLoading = false;
        _isGridVisible = true;

        if (items.isNotEmpty && selectedItem == null) {
          selectedItem = items[0];
          _showEditForm = true;
        }
      });
    } catch (e) {
      print('Error loading items: $e');
      if (mounted) {
        setState(() {
          isLoading = false;
          _isGridVisible = true;
        });
      }
    }
  }

  Future<void> handleDelete(String itemId) async {
    try {
      await supabase.from('food_table').delete().match({'food_id': itemId});

      if (mounted) {
        setState(() {
          items.removeWhere((item) => item['food_id'].toString() == itemId);

          if (selectedItem != null &&
              selectedItem!['food_id'].toString() == itemId) {
            if (items.isNotEmpty) {
              selectedItem = items[0];
              _showEditForm = true;
            } else {
              selectedItem = null;
              _showEditForm = false;
            }
          }
        });

        final controller = context.read<MenuScreenController>();
        await controller.handleItemDeleted(widget.category);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al eliminar el elemento: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(6),
        side: BorderSide(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Text(
                      widget.category,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${items.length}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[700],
                        ),
                      ),
                    ),
                  ],
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 20),
                  padding: EdgeInsets.zero,
                  onPressed: widget.onClose,
                ),
              ],
            ),
          ),
          Expanded(
            child: Row(
              children: [
                Expanded(
                  flex: _showEditForm ? 3 : 5,
                  child: _buildGrid(),
                ),
                if (_showEditForm && selectedItem != null)
                  Expanded(
                    flex: 3,
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border(
                          left: BorderSide(color: Colors.grey[300]!),
                        ),
                      ),
                      child: MenuForm(
                        key: ValueKey(selectedItem!['food_id']),
                        initialData: selectedItem,
                        onClose: () {
                          setState(() {
                            _showEditForm = false;
                            selectedItem = null;
                          });
                          _loadItems();
                        },
                        onSave: () {
                          _loadItems();
                        },
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGrid() {
    return isLoading
        ? const Center(child: CircularProgressIndicator())
        : AnimatedOpacity(
            duration: const Duration(milliseconds: 300),
            opacity: _isGridVisible ? 1.0 : 0.0,
            child: GridView.builder(
              padding: const EdgeInsets.all(8),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 6,
                childAspectRatio: 0.65,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
              ),
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                return _buildItemCard(item);
              },
            ),
          );
  }

  Widget _buildItemCard(Map<String, dynamic> item) {
    final isSelected =
        selectedItem != null && selectedItem!['food_id'] == item['food_id'];

    return Card(
      elevation: 0,
      color: isSelected ? Colors.blue.withOpacity(0.1) : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(6),
        side: BorderSide(color: Colors.grey[300]!),
      ),
      child: InkWell(
        onTap: () async {
          final updatedItem = await _getUpdatedItemData(item['food_id']);
          if (mounted) {
            setState(() {
              selectedItem = updatedItem ?? item;
              _showEditForm = true;
            });
          }
        },
        borderRadius: BorderRadius.circular(6),
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                flex: 5,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: item['food_photo'] != null
                      ? Image.network(
                          item['food_photo'],
                          width: double.infinity,
                          fit: BoxFit.cover,
                        )
                      : Container(
                          color: Colors.grey[200],
                          child: const Icon(Icons.image, size: 30),
                        ),
                ),
              ),
              const SizedBox(height: 0),
              Expanded(
                flex: 4,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item['food_name'] ?? '',
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 1),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '\$${(item['food_price'] ?? 0.0).toStringAsFixed(2)}',
                                style: TextStyle(
                                  fontSize: 10,
                                  color: Colors.green[700],
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.grey[100],
                                  borderRadius: BorderRadius.circular(4),
                                ),
                              ),
                            ],
                          ),
                          Text(
                            'Stock: ${item['food_stock'] ?? 0}',
                            style: TextStyle(
                              fontSize: 11,
                              color: Colors.grey[700],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.star,
                                size: 12, color: Colors.amber),
                            const SizedBox(width: 2),
                            Text(
                              (item['rate'] ?? 0.0).toStringAsFixed(1),
                              style: const TextStyle(fontSize: 11),
                            ),
                          ],
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete, size: 14),
                          onPressed: () => _showDeleteConfirmation(item),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
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
              handleDelete(item['food_id'].toString());
            },
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  Future<Map<String, dynamic>?> _getUpdatedItemData(int foodId) async {
    try {
      final response = await supabase.from('food_table').select('''
            food_id,
            food_name,
            food_price,sto
            food_photo,
            food_category,
            food_description,
            rate,
            food_stock
          ''').eq('food_id', foodId).single();
      return response;
    } catch (e) {
      print('Error fetching updated item data: $e');
      return null;
    }
  }
}
