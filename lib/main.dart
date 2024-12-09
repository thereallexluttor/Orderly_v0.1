import 'package:flutter/material.dart';
import 'package:orderly/presentation/screens/login.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner:
          false, // Desactiva el banner de debug en los dispositivos móviles
      home: LoginScreen(), // Establece la pantalla principal como LoginScreen
    ); // Fin de MaterialApp
  }
} // Fin de MyApp
