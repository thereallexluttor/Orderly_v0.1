import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:url_launcher/url_launcher.dart';

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

  void _showUsageHistory(Map<String, dynamic> item) async {
    try {
      final response = await http.get(
        Uri.parse(
            'http://localhost:8000/ingredient-usage/${item['ingredient_id']}'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final stats = IngredientStats.fromJson(data['stats']);

        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('Análisis de Uso - ${item['ingredient_name']}'),
            content: Container(
              width: 800,
              height: 600,
              child: Column(
                children: [
                  // Estadísticas generales
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildStatCard(
                            'Uso Total',
                            '${stats.totalUsage.toStringAsFixed(2)} ${item['unit']}',
                            Icons.assessment,
                          ),
                          _buildStatCard(
                            'Promedio Diario',
                            '${stats.avgDailyUsage.toStringAsFixed(2)} ${item['unit']}',
                            Icons.trending_up,
                          ),
                          _buildStatCard(
                            'Máximo Diario',
                            '${stats.maxDailyUsage.toStringAsFixed(2)} ${item['unit']}',
                            Icons.arrow_upward,
                          ),
                          _buildStatCard(
                            'Días Registrados',
                            stats.totalDays.toString(),
                            Icons.calendar_today,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Botón para ver gráficas en el navegador
                  ElevatedButton.icon(
                    onPressed: () async {
                      final url = Uri.parse(
                          'http://localhost:8000/ingredient-usage/${item['ingredient_id']}');
                      if (await canLaunchUrl(url)) {
                        await launchUrl(url);
                      }
                    },
                    icon: const Icon(Icons.bar_chart),
                    label: const Text('Ver Gráficas en el Navegador'),
                  ),
                ],
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
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al cargar las estadísticas: $e')),
      );
    }
  }

  Widget _buildStatCard(String title, String value, IconData icon) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 24, color: Colors.blue),
        const SizedBox(height: 8),
        Text(
          title,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 16,
            color: Colors.blue,
          ),
        ),
      ],
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

class IngredientStats {
  final double totalUsage;
  final double avgDailyUsage;
  final double maxDailyUsage;
  final int totalDays;

  IngredientStats({
    required this.totalUsage,
    required this.avgDailyUsage,
    required this.maxDailyUsage,
    required this.totalDays,
  });

  factory IngredientStats.fromJson(Map<String, dynamic> json) {
    return IngredientStats(
      totalUsage: json['total_usage'],
      avgDailyUsage: json['avg_daily_usage'],
      maxDailyUsage: json['max_daily_usage'],
      totalDays: json['total_days'],
    );
  }
}
