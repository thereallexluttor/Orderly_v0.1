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

class MyHomePage extends StatefulWidget {
  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  @override
  Widget build(BuildContext context) {
    // Get the current screen size
    final Size screenSize = MediaQuery.of(context).size;

    return Scaffold(
      body: Container(
        width: screenSize.width, // Use the full width of the screen
        height: screenSize.height, // Use the full height of the screen
        color: Colors.white,
        child: const Center(
          child: Text('Hello, World!'),
        ),
      ),
    );
  }
}
