import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'custom_text_field.dart';

class ImageUploadField extends StatelessWidget {
  final File? imageFile;
  final TextEditingController photoController;
  final Function(File) onImagePicked;

  const ImageUploadField({
    super.key,
    required this.imageFile,
    required this.photoController,
    required this.onImagePicked,
  });

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1024,
      maxHeight: 1024,
      imageQuality: 85,
    );
    if (image != null) {
      onImagePicked(File(image.path));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(8),
        color: Colors.white,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Food Image',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 20),
          if (imageFile != null) _buildImagePreview(),
          const SizedBox(height: 20),
          _buildImagePickerButton(),
          const SizedBox(height: 20),
          CustomTextField(
            controller: photoController,
            label: 'Photo URL (optional)',
          ),
        ],
      ),
    );
  }

  Widget _buildImagePreview() {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.grey.withOpacity(0.3),
              spreadRadius: 2,
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.file(
            imageFile!,
            fit: BoxFit.cover,
          ),
        ),
      ),
    );
  }

  Widget _buildImagePickerButton() {
    return ElevatedButton.icon(
      onPressed: _pickImage,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
        backgroundColor: Colors.white,
        foregroundColor: Colors.grey[800],
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: Colors.grey[300]!),
        ),
        elevation: 0,
      ),
      icon: const Icon(Icons.image_outlined),
      label: const Text(
        'Select Image',
        style: TextStyle(fontSize: 16),
      ),
    );
  }
}
