import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final _supabase = Supabase.instance.client;
  List<Map<String, dynamic>> _inventoryItems = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadInventoryData();
  }

  Future<void> _loadInventoryData() async {
    try {
      final response = await _supabase
          .from('inventory_table')
          .select()
          .order('ingredient_name');

      setState(() {
        _inventoryItems = response as List<Map<String, dynamic>>;
        _loading = false;
      });
    } catch (error) {
      debugPrint('Error loading inventory: $error');
      setState(() {
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inventario'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _inventoryItems.isEmpty
              ? const Center(
                  child: Text('No hay ingredientes en el inventario'))
              : SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('ID')),
                      DataColumn(label: Text('Food ID')),
                      DataColumn(label: Text('Nombre')),
                      DataColumn(label: Text('Cantidad por Unidad')),
                      DataColumn(label: Text('Unidad')),
                      DataColumn(label: Text('Stock Total')),
                    ],
                    rows: _inventoryItems.map((item) {
                      return DataRow(
                        cells: [
                          DataCell(
                              Text(item['ingredient_id']?.toString() ?? '')),
                          DataCell(Text(item['food_id']?.toString() ?? '')),
                          DataCell(Text(item['ingredient_name'] ?? '')),
                          DataCell(Text(
                              item['quantity_per_unit']?.toString() ?? '')),
                          DataCell(Text(item['unit'] ?? '')),
                          DataCell(Text(item['total_stock']?.toString() ?? '')),
                        ],
                      );
                    }).toList(),
                  ),
                ),
    );
  }
}
