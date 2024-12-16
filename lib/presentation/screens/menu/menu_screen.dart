import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';

class MenuScreen extends StatefulWidget {
  const MenuScreen({super.key});

  @override
  State<MenuScreen> createState() => _MenuScreenState();
}

class _MenuScreenState extends State<MenuScreen> {
  final _formKey = GlobalKey<FormState>();
  bool _showForm = false;
  bool _isLoading = false;

  // Get Supabase client
  final _supabase = Supabase.instance.client;

  // Controllers for form fields
  final _foodIdController = TextEditingController();
  final _nameController = TextEditingController();
  final _descController = TextEditingController();
  final _businessIdController = TextEditingController();
  final _rateController = TextEditingController();
  final _photoController = TextEditingController();
  final _priceController = TextEditingController();
  final _discountController = TextEditingController();
  final _categoryController = TextEditingController();
  final _stockController = TextEditingController();

  File? _imageFile;
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImage() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 85,
    );
    if (image != null) {
      setState(() {
        _imageFile = File(image.path);
      });
    }
  }

  Future<String?> _uploadImage() async {
    if (_imageFile == null) return null;

    try {
      final String fileName = '${DateTime.now().millisecondsSinceEpoch}.jpg';
      final String path = 'menu_images/$fileName';

      // Convertir el archivo a bytes
      final bytes = await _imageFile!.readAsBytes();

      // Subir la imagen al bucket con mejor manejo de errores
      try {
        await _supabase.storage.from('orderly_menu').uploadBinary(
              path,
              bytes,
              fileOptions: const FileOptions(
                contentType: 'image/jpeg',
              ),
            );
      } catch (storageError) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Storage Error: ${storageError.toString()}'),
              backgroundColor: Colors.red,
            ),
          );
        }
        return null;
      }

      // Obtener la URL pública de la imagen
      try {
        final String imageUrl =
            _supabase.storage.from('orderly_menu').getPublicUrl(path);
        return imageUrl;
      } catch (urlError) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('URL Error: ${urlError.toString()}'),
              backgroundColor: Colors.red,
            ),
          );
        }
        return null;
      }
    } catch (e) {
      print('Error detallado: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error uploading image: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
      return null;
    }
  }

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        // Subir imagen si existe
        String? imageUrl;
        if (_imageFile != null) {
          imageUrl = await _uploadImage();
        }

        // Create data map
        final foodData = {
          'food_id': int.tryParse(_foodIdController.text),
          'food_name': _nameController.text,
          'food_desc': _descController.text,
          'business_id': _businessIdController.text,
          'rate': double.tryParse(_rateController.text),
          'food_photo': imageUrl ??
              _photoController.text, // Usar la URL de la imagen subida
          'food_price': double.tryParse(_priceController.text),
          'food_discount': double.tryParse(_discountController.text),
          'food_category': _categoryController.text,
          'food_stock': int.tryParse(_stockController.text),
        };

        // Insert data into Supabase
        final response =
            await _supabase.from('food_table').insert(foodData).select();

        // Clear form after successful submission
        _clearForm();

        // Show success message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Food item added successfully!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } catch (e) {
        // Show error message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Error: ${e.toString()}'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  void _clearForm() {
    _foodIdController.clear();
    _nameController.clear();
    _descController.clear();
    _businessIdController.clear();
    _rateController.clear();
    _photoController.clear();
    _priceController.clear();
    _discountController.clear();
    _categoryController.clear();
    _stockController.clear();
  }

  Widget _buildImageUploadField() {
    return Column(
      children: [
        if (_imageFile != null)
          Container(
            height: 200,
            width: double.infinity,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.grey),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Image.file(
              _imageFile!,
              fit: BoxFit.cover,
            ),
          ),
        const SizedBox(height: 10),
        ElevatedButton.icon(
          onPressed: _pickImage,
          icon: const Icon(Icons.image),
          label: const Text('Select Image'),
        ),
        const SizedBox(height: 10),
        TextFormField(
          controller: _photoController,
          decoration: const InputDecoration(
            labelText: 'Photo URL (optional)',
            hintText: 'Or enter image URL manually',
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _showForm = !_showForm;
                });
              },
              child: Text(_showForm ? 'Hide Form' : 'Show Form'),
            ),
            if (_showForm)
              Expanded(
                child: SingleChildScrollView(
                  child: Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        TextFormField(
                          controller: _foodIdController,
                          decoration:
                              const InputDecoration(labelText: 'Food ID'),
                          keyboardType: TextInputType.number,
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a Food ID';
                            }
                            return null;
                          },
                        ),
                        TextFormField(
                          controller: _nameController,
                          decoration:
                              const InputDecoration(labelText: 'Food Name'),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a food name';
                            }
                            return null;
                          },
                        ),
                        TextFormField(
                          controller: _descController,
                          decoration:
                              const InputDecoration(labelText: 'Description'),
                          maxLines: 3,
                        ),
                        TextFormField(
                          controller: _businessIdController,
                          decoration:
                              const InputDecoration(labelText: 'Business ID'),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a Business ID';
                            }
                            return null;
                          },
                        ),
                        TextFormField(
                          controller: _rateController,
                          decoration: const InputDecoration(labelText: 'Rate'),
                          keyboardType: TextInputType.number,
                        ),
                        _buildImageUploadField(),
                        TextFormField(
                          controller: _priceController,
                          decoration: const InputDecoration(labelText: 'Price'),
                          keyboardType: TextInputType.number,
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a price';
                            }
                            return null;
                          },
                        ),
                        TextFormField(
                          controller: _discountController,
                          decoration:
                              const InputDecoration(labelText: 'Discount'),
                          keyboardType: TextInputType.number,
                        ),
                        TextFormField(
                          controller: _categoryController,
                          decoration:
                              const InputDecoration(labelText: 'Category'),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a category';
                            }
                            return null;
                          },
                        ),
                        TextFormField(
                          controller: _stockController,
                          decoration: const InputDecoration(labelText: 'Stock'),
                          keyboardType: TextInputType.number,
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter stock quantity';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),
                        ElevatedButton(
                          onPressed: _isLoading ? null : _submitForm,
                          child: _isLoading
                              ? const CircularProgressIndicator()
                              : const Text('Submit'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _foodIdController.dispose();
    _nameController.dispose();
    _descController.dispose();
    _businessIdController.dispose();
    _rateController.dispose();
    _photoController.dispose();
    _priceController.dispose();
    _discountController.dispose();
    _categoryController.dispose();
    _stockController.dispose();
    super.dispose();
  }
}
