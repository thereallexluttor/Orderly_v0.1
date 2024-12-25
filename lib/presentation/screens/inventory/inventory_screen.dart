import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:intl/intl.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final _supabase = Supabase.instance.client;
  List<Map<String, dynamic>> _inventoryItems = [];
  Map<int, double> _ingredientUsage = {};
  bool _loading = true;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadInventoryData();
  }

  Future<void> _loadInventoryData() async {
    try {
      // Modificamos la consulta para solo incluir la relación con ingredient_usage_table
      final response = await _supabase.from('inventory_table').select('''
            *,
            ingredient_usage_table(
              quantity_used,
              usage_date
            )
          ''').order('ingredient_name');

      // Calcular uso total por ingrediente
      final items = response as List<Map<String, dynamic>>;
      final usageMap = <int, double>{};

      for (var item in items) {
        final ingredientId = item['ingredient_id'] as int;
        final usageList = item['ingredient_usage_table'] as List;

        double totalUsage = 0;
        for (var usage in usageList) {
          totalUsage += (usage['quantity_used'] as num).toDouble();
        }

        usageMap[ingredientId] = totalUsage;
      }

      setState(() {
        _inventoryItems = items;
        _ingredientUsage = usageMap;
        _loading = false;
      });
    } catch (error) {
      debugPrint('Error loading inventory: $error');
      setState(() {
        _loading = false;
      });
    }
  }

  double getAvailableStock(Map<String, dynamic> item) {
    final totalStock = (item['total_stock'] as num).toDouble();
    final usage = _ingredientUsage[item['ingredient_id']] ?? 0.0;
    return totalStock - usage;
  }

  List<Map<String, dynamic>> get _filteredItems => _inventoryItems
      .where((item) => item['ingredient_name']
          .toString()
          .toLowerCase()
          .contains(_searchQuery.toLowerCase()))
      .toList();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Inventario',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            _buildTopBar(),
            const SizedBox(height: 24),
            _buildInventoryHeader(),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _buildInventoryList(),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Implementar añadir nuevo ingrediente
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildInventoryHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Row(
        children: [
          Expanded(
              flex: 3,
              child: Text('Ingrediente',
                  style: TextStyle(fontWeight: FontWeight.bold))),
          Expanded(
              flex: 2,
              child: Text('Stock Inicial',
                  style: TextStyle(fontWeight: FontWeight.bold))),
          Expanded(
              flex: 2,
              child: Text('Stock Disponible',
                  style: TextStyle(fontWeight: FontWeight.bold))),
          Expanded(
              flex: 2,
              child: Text('Uso Total',
                  style: TextStyle(fontWeight: FontWeight.bold))),
          Expanded(
              flex: 1,
              child: Text('Estado',
                  style: TextStyle(fontWeight: FontWeight.bold))),
          SizedBox(width: 100),
        ],
      ),
    );
  }

  Widget _buildInventoryList() {
    return ListView.builder(
      itemCount: _filteredItems.length,
      itemBuilder: (context, index) {
        final item = _filteredItems[index];
        final availableStock = getAvailableStock(item);
        final totalUsage = _ingredientUsage[item['ingredient_id']] ?? 0.0;
        final isLowStock = availableStock < 10; // Umbral de stock bajo

        return Card(
          margin: const EdgeInsets.symmetric(vertical: 4),
          child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            title: Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item['ingredient_name'] ?? '',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        'ID: ${item['ingredient_id']} | Unidad: ${item['unit']}',
                        style: TextStyle(color: Colors.grey[600], fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Text('${item['total_stock']} ${item['unit']}'),
                ),
                Expanded(
                  flex: 2,
                  child: Text(
                    '${availableStock.toStringAsFixed(2)} ${item['unit']}',
                    style: TextStyle(
                      color: isLowStock ? Colors.red : null,
                      fontWeight: isLowStock ? FontWeight.bold : null,
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child:
                      Text('${totalUsage.toStringAsFixed(2)} ${item['unit']}'),
                ),
                Expanded(
                  flex: 1,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: isLowStock ? Colors.red[100] : Colors.green[100],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      isLowStock ? 'Bajo' : 'OK',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: isLowStock ? Colors.red[900] : Colors.green[900],
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                SizedBox(
                  width: 100,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.edit_outlined, size: 20),
                        onPressed: () {
                          // TODO: Implementar edición
                        },
                        tooltip: 'Editar',
                      ),
                      IconButton(
                        icon: const Icon(Icons.history, size: 20),
                        onPressed: () => _showUsageHistory(item),
                        tooltip: 'Historial',
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showUsageHistory(Map<String, dynamic> item) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Historial de Uso - ${item['ingredient_name']}'),
        content: SizedBox(
          width: 600,
          height: 400,
          child: ListView.builder(
            itemCount: (item['ingredient_usage_table'] as List).length,
            itemBuilder: (context, index) {
              final usage = (item['ingredient_usage_table'] as List)[index];
              return ListTile(
                title: Text(
                    'Cantidad usada: ${usage['quantity_used']} ${item['unit']}'),
                subtitle: Text(
                    'Fecha: ${DateFormat('dd/MM/yyyy').format(DateTime.parse(usage['usage_date']))}'),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }

  Widget _buildTopBar() {
    return Row(
      children: [
        Expanded(
          child: TextField(
            decoration: InputDecoration(
              hintText: 'Buscar ingrediente...',
              prefixIcon: const Icon(Icons.search),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Colors.grey[100],
            ),
            onChanged: (value) {
              setState(() {
                _searchQuery = value;
              });
            },
          ),
        ),
        const SizedBox(width: 16),
        _buildFilterButton(),
        const SizedBox(width: 16),
        _buildSortButton(),
      ],
    );
  }

  Widget _buildFilterButton() {
    return ElevatedButton.icon(
      onPressed: () {
        // TODO: Implementar filtros
      },
      icon: const Icon(Icons.filter_list),
      label: const Text('Filtrar'),
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }

  Widget _buildSortButton() {
    return ElevatedButton.icon(
      onPressed: () {
        // TODO: Implementar ordenamiento
      },
      icon: const Icon(Icons.sort),
      label: const Text('Ordenar'),
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}
