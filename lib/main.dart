import 'package:flutter/material.dart';
import 'package:orderly/presentation/screens/login.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'presentation/screens/homepage.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment variables
  await dotenv.load(fileName: ".env");

  // Initialize Supabase
  await Supabase.initialize(
    url: dotenv.env['SUPABASE_URL']!,
    anonKey: dotenv.env['SUPABASE_ANON_KEY']!,
  );

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner:
          false, // Desactiva el banner de debug en los dispositivos móviles
      home:
          const LoginScreen(), // Establece la pantalla principal como LoginScreen
      routes: {
        HomePage.routeName: (context) => const HomePage(),
        // ... otras rutas
      },
    ); // Fin de MaterialApp
  }
} // Fin de MyApp

