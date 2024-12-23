import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class MenuScreenController extends ChangeNotifier {
  final supabase = Supabase.instance.client;
  bool isLoading = false;
  bool showForm = false;
  String? selectedCategory;
  List<Map<String, dynamic>> categories = [];

  Future<void> handleItemDeleted(String category) async {
    final response = await supabase
        .from('food_table')
        .select('food_category')
        .eq('food_category', category);

    final itemsInCategory = response as List;

    if (itemsInCategory.isEmpty) {
      selectedCategory = null;
      await loadCategories();
    } else {
      await loadCategories();
    }

    notifyListeners();
  }

  void toggleForm() {
    showForm = !showForm;
    notifyListeners();
  }

  void selectCategory(String? category) {
    selectedCategory = category;
    notifyListeners();
  }

  Future<void> loadCategories() async {
    if (isLoading) return;

    isLoading = true;
    notifyListeners();

    try {
      final response = await supabase
          .from('food_table')
          .select('food_category, food_photo, rate')
          .order('rate', ascending: false);

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

      categories = categoryMap.values.toList();

      if (selectedCategory != null &&
          !categories.any((cat) => cat['food_category'] == selectedCategory)) {
        selectedCategory = null;
      }

      isLoading = false;
      notifyListeners();
    } catch (e) {
      isLoading = false;
      notifyListeners();
      throw Exception('Error loading categories: $e');
    }
  }

  Future<void> handleItemSaved() async {
    await loadCategories();
    notifyListeners();
  }
}
