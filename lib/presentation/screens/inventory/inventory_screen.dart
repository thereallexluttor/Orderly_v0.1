import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

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
      return totalStock - usage;
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
        final totalStock = (item['total_stock'] as num?)?.toDouble() ?? 0.0;
        final safeFactor = (item['safe_factor'] as num?)?.toDouble() ?? 10.0;

        // Calcula el umbral de stock bajo basado en el safe_factor
        final safeThreshold = totalStock * (safeFactor / 100);
        final isLowStock = availableStock < safeThreshold;

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

  void _showUsageHistory(Map<String, dynamic> item) {
    final totalUsage = _ingredientUsage[item['ingredient_id']] ?? 0.0;
    final usageList = item['ingredient_usage_table'] as List;

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

    // Calcular estadísticas básicas
    double maxDailyUsage = 0;
    Map<String, double> dailyUsage = {};

    for (var usage in usageList) {
      final date = DateTime.parse(usage['usage_date']).toLocal();
      final dateStr = date.toString().split(' ')[0];
      final quantity = (usage['quantity_used'] as num).toDouble();

      dailyUsage[dateStr] = (dailyUsage[dateStr] ?? 0) + quantity;
      if (dailyUsage[dateStr]! > maxDailyUsage) {
        maxDailyUsage = dailyUsage[dateStr]!;
      }
    }

    final avgDailyUsage = totalUsage / dailyUsage.length;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(7),
          side: BorderSide(color: Colors.grey[200]!),
        ),
        title: Text('Estadísticas de Uso - ${item['ingredient_name']}'),
        content: Container(
          width: 600,
          height: 400,
          child: Column(
            children: [
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
                        '${totalUsage.toStringAsFixed(2)} ${item['unit']}',
                        Icons.assessment,
                      ),
                      _buildStatCard(
                        'Promedio Diario',
                        '${avgDailyUsage.toStringAsFixed(2)} ${item['unit']}',
                        Icons.trending_up,
                      ),
                      _buildStatCard(
                        'Máximo Diario',
                        '${maxDailyUsage.toStringAsFixed(2)} ${item['unit']}',
                        Icons.arrow_upward,
                      ),
                      _buildStatCard(
                        'Días Registrados',
                        dailyUsage.length.toString(),
                        Icons.calendar_today,
                      ),
                    ],
                  ),
                ),
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
            child: Text('Cerrar', style: TextStyle(color: Colors.grey[800])),
          ),
        ],
      ),
    );
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
        const SizedBox(width: 16),
        ElevatedButton.icon(
          onPressed: () async {
            try {
              // Mostrar indicador de carga
              showDialog(
                context: context,
                barrierDismissible: false,
                builder: (BuildContext context) {
                  return Center(
                    child: Card(
                      child: Container(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: const [
                            CircularProgressIndicator(),
                            SizedBox(height: 16),
                            Text('Generando informe de inventario...')
                          ],
                        ),
                      ),
                    ),
                  );
                },
              );

              // Llamar a la API local de FastAPI
              final response = await http.get(
                Uri.parse('http://localhost:8000/inventory-report'),
              );

              // Cerrar el diálogo de carga
              Navigator.of(context).pop();

              if (response.statusCode == 200) {
                final data = json.decode(response.body);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(data['message']),
                    backgroundColor: Colors.green,
                  ),
                );
              } else {
                throw Exception(
                    'Error al generar el informe: ${response.statusCode}');
              }
            } catch (error) {
              // Cerrar el diálogo de carga si hay error
              Navigator.of(context).pop();

              // Mostrar error
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Error: ${error.toString()}'),
                  backgroundColor: Colors.red,
                ),
              );
            }
          },
          icon: const Text('👷‍♂️'),
          label: const Text('Generar Informe IA'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: Colors.grey[800],
            elevation: 0,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(7),
              side: BorderSide(color: Colors.grey[200]!),
            ),
          ),
        ),
      ],
    );
  }
}
