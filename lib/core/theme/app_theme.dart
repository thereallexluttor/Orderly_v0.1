import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData get lightTheme {
    // Define base font sizes
    const double scaleFactor = 0.9;

    return ThemeData(
      fontFamily: 'Poppins',
      textTheme: TextTheme(
        displayLarge: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 96 * scaleFactor),
        displayMedium: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 60 * scaleFactor),
        displaySmall: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 48 * scaleFactor),
        headlineLarge: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 40 * scaleFactor),
        headlineMedium: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 34 * scaleFactor),
        headlineSmall: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 24 * scaleFactor),
        titleLarge: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 20 * scaleFactor),
        titleMedium: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 16 * scaleFactor),
        titleSmall: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 14 * scaleFactor),
        bodyLarge: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 16 * scaleFactor),
        bodyMedium: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 14 * scaleFactor),
        bodySmall: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 12 * scaleFactor),
        labelLarge: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 14 * scaleFactor),
        labelMedium: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 12 * scaleFactor),
        labelSmall: const TextStyle(fontFamily: 'Poppins')
            .copyWith(fontSize: 11 * scaleFactor),
      ),
    );
  }
}
