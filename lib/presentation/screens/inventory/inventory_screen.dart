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
    try {
      final totalStock = (item['total_stock'] as num?)?.toDouble() ?? 0.0;
      final usage = _ingredientUsage[item['ingredient_id']] ?? 0.0;
      return (totalStock - usage).abs();
    } catch (e) {
      print('Error calculando stock disponible: $e');
      return 0.0;
    }
  }

  List<Map<String, dynamic>> get _filteredItems {
    var items = _inventoryItems
        .where((item) => item['ingredient_name']
            .toString()
            .toLowerCase()
            .contains(_searchQuery.toLowerCase()))
        .toList();

    // Ordenar por uso total (de mayor a menor)
    items.sort((a, b) {
      final usageA = _ingredientUsage[a['ingredient_id']] ?? 0.0;
      final usageB = _ingredientUsage[b['ingredient_id']] ?? 0.0;
      return usageB.compareTo(usageA);
    });

    return items;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
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
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(7),
          side: BorderSide(color: Colors.grey[200]!),
        ),
        onPressed: () async {
          final url = Uri.parse('http://localhost:8000/inventory-report');
          if (await canLaunchUrl(url)) {
            await launchUrl(url);
          } else {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('No se pudo abrir el reporte'),
                backgroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(7),
                  side: BorderSide(color: Colors.red[200]!),
                ),
                behavior: SnackBarBehavior.floating,
                margin: EdgeInsets.all(8),
                elevation: 0,
              ),
            );
          }
        },
        icon: Icon(Icons.assessment, color: Colors.grey[800]),
        label: Text(
          'Ver Reporte de Inventario',
          style: TextStyle(color: Colors.grey[800]),
        ),
      ),
    );
  }

  Widget _buildInventoryHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: Colors.grey[200]!),
        borderRadius: BorderRadius.circular(7),
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
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(7),
            side: BorderSide(color: Colors.grey[200]!),
          ),
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
                  child: GestureDetector(
                    onTap: () {
                      if (totalUsage == 0) {
                        showDialog(
                          context: context,
                          builder: (context) => AlertDialog(
                            backgroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(7),
                              side: BorderSide(color: Colors.grey[200]!),
                            ),
                            title: Text('Sin datos de uso'),
                            content: Text(
                                'Este ingrediente no tiene registros de uso hasta el momento.'),
                            actions: [
                              TextButton(
                                style: TextButton.styleFrom(
                                  backgroundColor: Colors.white,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(7),
                                    side: BorderSide(color: Colors.grey[200]!),
                                  ),
                                ),
                                onPressed: () => Navigator.pop(context),
                                child: Text('Cerrar',
                                    style: TextStyle(color: Colors.grey[800])),
                              ),
                            ],
                          ),
                        );
                      }
                    },
                    child: Text(
                      '${totalUsage.toStringAsFixed(2)} ${item['unit']}',
                      style: totalUsage == 0
                          ? TextStyle(
                              color: Colors.grey[400],
                              fontStyle: FontStyle.italic,
                            )
                          : null,
                    ),
                  ),
                ),
                Expanded(
                  flex: 1,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border.all(
                        color:
                            isLowStock ? Colors.red[200]! : Colors.green[200]!,
                      ),
                      borderRadius: BorderRadius.circular(7),
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
                        icon: Icon(Icons.history,
                            size: 20, color: Colors.grey[600]),
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
    final totalUsage = _ingredientUsage[item['ingredient_id']] ?? 0.0;

    if (totalUsage == 0) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          backgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(7),
            side: BorderSide(color: Colors.grey[200]!),
          ),
          title: Text('Sin datos de uso'),
          content: Text(
              'Este ingrediente no tiene registros de uso hasta el momento.'),
          actions: [
            TextButton(
              style: TextButton.styleFrom(
                backgroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(7),
                  side: BorderSide(color: Colors.grey[200]!),
                ),
              ),
              onPressed: () => Navigator.pop(context),
              child: Text('Cerrar', style: TextStyle(color: Colors.grey[800])),
            ),
          ],
        ),
      );
      return;
    }

    try {
      final availableStock = getAvailableStock(item);
      print('Stock disponible calculado: $availableStock'); // Debug log

      final uri = Uri.parse(
              'http://localhost:8000/ingredient-usage/${item['ingredient_id']}')
          .replace(queryParameters: {
        'current_stock': availableStock.toString(),
      });

      print('URL de la solicitud: $uri'); // Debug log

      final response = await http.get(uri);
      print('Código de respuesta: ${response.statusCode}'); // Debug log
      if (response.statusCode != 200) {
        print('Cuerpo de la respuesta de error: ${response.body}'); // Debug log
      }

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final stats = IngredientStats.fromJson(data['stats']);

        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            backgroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(7),
              side: BorderSide(color: Colors.grey[200]!),
            ),
            title: Text('Análisis de Uso - ${item['ingredient_name']}'),
            content: Container(
              width: 800,
              height: 600,
              color: Colors.white,
              child: Column(
                children: [
                  // Alerta de reabastecimiento
                  if (data['stats']['restock_status'] != null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        border: Border.all(color: Colors.grey[200]!),
                        borderRadius: BorderRadius.circular(7),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Estado del Stock',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          SizedBox(height: 8),
                          Text(data['stats']['restock_status']
                                  ['recommendation'] ??
                              'No hay recomendación disponible'),
                          SizedBox(height: 8),
                          if (data['stats']['restock_status']
                                  ['days_remaining'] !=
                              null)
                            Text(
                              'Días estimados de stock: ${data['stats']['restock_status']['days_remaining'].toStringAsFixed(1)}',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                        ],
                      ),
                    ),
                  // Estadísticas generales
                  Card(
                    elevation: 0,
                    color: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(7),
                      side: BorderSide(color: Colors.grey[200]!),
                    ),
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
                    style: ElevatedButton.styleFrom(
                      elevation: 0,
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.grey[800],
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(7),
                        side: BorderSide(color: Colors.grey[200]!),
                      ),
                    ),
                    onPressed: () async {
                      final availableStock = getAvailableStock(item);
                      final url = Uri.parse(
                              'http://localhost:8000/ingredient-usage/${item['ingredient_id']}')
                          .replace(queryParameters: {
                        'current_stock': availableStock.toString(),
                      });

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
                style: TextButton.styleFrom(
                  backgroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(7),
                    side: BorderSide(color: Colors.grey[200]!),
                  ),
                ),
                onPressed: () => Navigator.pop(context),
                child:
                    Text('Cerrar', style: TextStyle(color: Colors.grey[800])),
              ),
            ],
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                'Error al cargar las estadísticas. Código: ${response.statusCode}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      print('Error detallado: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al cargar las estadísticas: $e'),
          backgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(7),
            side: BorderSide(color: Colors.red[200]!),
          ),
          behavior: SnackBarBehavior.floating,
          margin: EdgeInsets.all(8),
          elevation: 0,
        ),
      );
    }
  }

  Color _getAlertColor(String urgency) {
    switch (urgency) {
      case 'high':
        return Colors.red[100]!;
      case 'medium':
        return Colors.orange[100]!;
      case 'low':
        return Colors.green[100]!;
      default:
        return Colors.grey[100]!;
    }
  }

  Widget _buildStatCard(String title, String value, IconData icon) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 24, color: Colors.grey[800]),
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
          style: TextStyle(
            fontSize: 16,
            color: Colors.grey[800],
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
              prefixIcon: Icon(Icons.search, color: Colors.grey[600]),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(7),
                borderSide: BorderSide(color: Colors.grey[200]!),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(7),
                borderSide: BorderSide(color: Colors.grey[200]!),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(7),
                borderSide: BorderSide(color: Colors.grey[400]!),
              ),
              filled: true,
              fillColor: Colors.white,
            ),
            onChanged: (value) {
              setState(() {
                _searchQuery = value;
              });
            },
          ),
        ),
      ],
    );
  }
}

class IngredientStats {
  final double totalUsage;
  final double avgDailyUsage;
  final double maxDailyUsage;
  final int totalDays;
  final double currentStock;
  final double daysRemaining;

  IngredientStats({
    required this.totalUsage,
    required this.avgDailyUsage,
    required this.maxDailyUsage,
    required this.totalDays,
    this.currentStock = 0.0,
    this.daysRemaining = 0.0,
  });

  factory IngredientStats.fromJson(Map<String, dynamic> json) {
    return IngredientStats(
      totalUsage: (json['total_usage'] ?? 0).toDouble(),
      avgDailyUsage: (json['avg_daily_usage'] ?? 0).toDouble(),
      maxDailyUsage: (json['max_daily_usage'] ?? 0).toDouble(),
      totalDays: json['total_days'] ?? 0,
      currentStock: (json['restock_status']?['current_stock'] ?? 0).toDouble(),
      daysRemaining:
          (json['restock_status']?['days_remaining'] ?? 0).toDouble(),
    );
  }
}
