import 'package:flutter/material.dart';
import '../controllers/menu_form_controller.dart';
import 'custom_text_field.dart';
import 'image_upload_field.dart';

class MenuForm extends StatefulWidget {
  final VoidCallback onClose;

  const MenuForm({
    super.key,
    required this.onClose,
  });

  @override
  State<MenuForm> createState() => _MenuFormState();
}

class _MenuFormState extends State<MenuForm> {
  final _controller = MenuFormController();
  bool _isLoading = false;

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

        await _controller.supabase.from('food_table').insert(foodData).select();

        _controller.clearForm();
        _showSuccessMessage();
      } catch (e) {
        _showErrorMessage(e.toString());
      } finally {
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    }
  }

  void _showSuccessMessage() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Food item added successfully!'),
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
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(32.0),
        child: Form(
          key: _controller.formKey,
          child: Column(
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
            label: 'Rate',
            keyboardType: TextInputType.number,
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
            label: 'Price',
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter a price';
              }
              return null;
            },
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: CustomTextField(
            controller: _controller.discountController,
            label: 'Discount',
            keyboardType: TextInputType.number,
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
            label: 'Stock',
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Please enter stock quantity';
              }
              return null;
            },
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
