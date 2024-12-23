import 'package:flutter/material.dart';
import '../controllers/menu_form_controller.dart';
import 'custom_text_field.dart';
import 'image_upload_field.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../controllers/menu_screen_controller.dart';

class MenuForm extends StatefulWidget {
  final VoidCallback onClose;
  final Map<String, dynamic>? initialData;
  final VoidCallback? onSave;

  const MenuForm({
    super.key,
    required this.onClose,
    this.initialData,
    this.onSave,
  });

  @override
  State<MenuForm> createState() => _MenuFormState();
}

class _MenuFormState extends State<MenuForm> {
  final _controller = MenuFormController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialData != null) {
      _controller.foodIdController.text =
          widget.initialData!['food_id'].toString();
      _controller.nameController.text = widget.initialData!['food_name'] ?? '';
      _controller.descController.text = widget.initialData!['food_desc'] ?? '';
      _controller.businessIdController.text =
          widget.initialData!['business_id'] ?? '';
      _controller.rateController.text =
          widget.initialData!['rate']?.toString() ?? '';
      _controller.photoController.text =
          widget.initialData!['food_photo'] ?? '';
      _controller.priceController.text =
          widget.initialData!['food_price']?.toString() ?? '';
      _controller.discountController.text =
          widget.initialData!['food_discount']?.toString() ?? '';
      _controller.categoryController.text =
          widget.initialData!['food_category'] ?? '';
      _controller.stockController.text =
          widget.initialData!['food_stock']?.toString() ?? '';
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submitForm() async {
    if (_controller.formKey.currentState!.validate()) {
      setState(() => _isLoading = true);

      try {
        final imageUrl = await _controller.uploadImage();
        final foodData = _controller.getFormData(imageUrl);

        if (widget.initialData != null) {
          await _controller.supabase
              .from('food_table')
              .update(foodData)
              .eq('food_id', widget.initialData!['food_id']);
          _showSuccessMessage('Food item updated successfully!');
        } else {
          await _controller.supabase
              .from('food_table')
              .insert(foodData)
              .select();
          _showSuccessMessage('Food item added successfully!');
        }

        if (context.mounted) {
          final controller = context.read<MenuScreenController>();
          await controller.handleItemSaved();
        }

        _controller.clearForm();
        widget.onClose();
        widget.onSave?.call();
      } catch (e) {
        _showErrorMessage(e.toString());
      } finally {
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    }
  }

  void _showSuccessMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _showErrorMessage(String error) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Error: $error'),
        backgroundColor: Colors.red,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shadowColor: Colors.black.withOpacity(0.1),
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.grey[300]!),
      ),
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * 0.8,
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32.0),
          child: Form(
            key: _controller.formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildBasicInfo(),
                const SizedBox(height: 24),
                _buildDescription(),
                const SizedBox(height: 24),
                _buildBusinessInfo(),
                const SizedBox(height: 24),
                ImageUploadField(
                  imageFile: _controller.imageFile,
                  photoController: _controller.photoController,
                  onImagePicked: (file) =>
                      setState(() => _controller.imageFile = file),
                ),
                const SizedBox(height: 24),
                _buildPricing(),
                const SizedBox(height: 24),
                _buildCategoryAndStock(),
                const SizedBox(height: 32),
                _buildSubmitButton(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBasicInfo() {
    return Row(
      children: [
        Expanded(
          child: CustomTextField(
            controller: _controller.foodIdController,
            label: 'Food ID',
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a Food ID';
              }
              return null;
            },
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: CustomTextField(
            controller: _controller.nameController,
            label: 'Food Name',
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a food name';
              }
              return null;
            },
          ),
        ),
      ],
    );
  }

  Widget _buildDescription() {
    return CustomTextField(
      controller: _controller.descController,
      label: 'Description',
      maxLines: 3,
    );
  }

  Widget _buildBusinessInfo() {
    return Row(
      children: [
        Expanded(
          child: CustomTextField(
            controller: _controller.businessIdController,
            label: 'Business ID',
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a Business ID';
              }
              return null;
            },
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: CustomTextField(
            controller: _controller.rateController,
            label: 'Rate (0-5)',
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return null; // Rate puede ser opcional
              }
              final rate = int.tryParse(value);
              if (rate == null || rate < 0 || rate > 5) {
                return 'Rate must be between 0 and 5';
              }
              return null;
            },
            suffix: const Icon(Icons.star_border),
          ),
        ),
      ],
    );
  }

  Widget _buildPricing() {
    return Row(
      children: [
        Expanded(
          child: CustomTextField(
            controller: _controller.priceController,
            label: 'Price (\$)',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a price';
              }
              final price = double.tryParse(value);
              if (price == null || price < 0) {
                return 'Please enter a valid price';
              }
              return null;
            },
            prefix: const Text('\$'),
            inputFormatters: [
              FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}')),
            ],
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: CustomTextField(
            controller: _controller.discountController,
            label: 'Discount (%)',
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return null; // Descuento puede ser opcional
              }
              final discount = int.tryParse(value);
              if (discount == null || discount < 0 || discount > 100) {
                return 'Discount must be between 0 and 100';
              }
              return null;
            },
            suffix: const Text('%'),
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCategoryAndStock() {
    return Row(
      children: [
        Expanded(
          child: CustomTextField(
            controller: _controller.categoryController,
            label: 'Category',
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a category';
              }
              return null;
            },
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: CustomTextField(
            controller: _controller.stockController,
            label: 'Stock (Units)',
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter stock quantity';
              }
              final stock = int.tryParse(value);
              if (stock == null || stock < 0) {
                return 'Stock must be a positive number';
              }
              return null;
            },
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
            ],
            suffix: const Text('units'),
          ),
        ),
      ],
    );
  }

  Widget _buildSubmitButton() {
    return SizedBox(
      height: 50,
      child: ElevatedButton(
        onPressed: _isLoading ? null : _submitForm,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromARGB(255, 255, 255, 255),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(4),
            side: BorderSide(color: Colors.grey[300]!),
          ),
          elevation: 0,
        ),
        child: _isLoading
            ? const CircularProgressIndicator(
                color: Colors.grey,
              )
            : const Text(
                'Save Menu Item',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.normal,
                  color: Colors.black87,
                ),
              ),
      ),
    );
  }
}
