import 'package:flutter/material.dart';
import 'package:orderly/presentation/screens/login.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // Desactiva el banner
      home: LoginScreen(),
    );
  }
}
