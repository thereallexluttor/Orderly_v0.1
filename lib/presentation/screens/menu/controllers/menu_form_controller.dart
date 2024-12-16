import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'dart:io';

class MenuFormController {
  final formKey = GlobalKey<FormState>();
  final supabase = Supabase.instance.client;

  // Form Controllers
  final foodIdController = TextEditingController();
  final nameController = TextEditingController();
  final descController = TextEditingController();
  final businessIdController = TextEditingController();
  final rateController = TextEditingController();
  final photoController = TextEditingController();
  final priceController = TextEditingController();
  final discountController = TextEditingController();
  final categoryController = TextEditingController();
  final stockController = TextEditingController();

  File? imageFile;

  Future<String?> uploadImage() async {
    if (imageFile == null) return null;

    try {
      final String fileName = '${DateTime.now().millisecondsSinceEpoch}.jpg';
      final String path = 'menu_images/$fileName';
      final bytes = await imageFile!.readAsBytes();

      await supabase.storage.from('orderly_menu').uploadBinary(
            path,
            bytes,
            fileOptions: const FileOptions(contentType: 'image/jpeg'),
          );

      return supabase.storage.from('orderly_menu').getPublicUrl(path);
    } catch (e) {
      print('Error uploading image: $e');
      return null;
    }
  }

  Map<String, dynamic> getFormData(String? imageUrl) {
    return {
      'food_id': int.tryParse(foodIdController.text),
      'food_name': nameController.text,
      'food_desc': descController.text,
      'business_id': businessIdController.text,
      'rate': double.tryParse(rateController.text),
      'food_photo': imageUrl ?? photoController.text,
      'food_price': double.tryParse(priceController.text),
      'food_discount': double.tryParse(discountController.text),
      'food_category': categoryController.text,
      'food_stock': int.tryParse(stockController.text),
    };
  }

  void clearForm() {
    foodIdController.clear();
    nameController.clear();
    descController.clear();
    businessIdController.clear();
    rateController.clear();
    photoController.clear();
    priceController.clear();
    discountController.clear();
    categoryController.clear();
    stockController.clear();
    imageFile = null;
  }

  void dispose() {
    foodIdController.dispose();
    nameController.dispose();
    descController.dispose();
    businessIdController.dispose();
    rateController.dispose();
    photoController.dispose();
    priceController.dispose();
    discountController.dispose();
    categoryController.dispose();
    stockController.dispose();
  }
}
