import 'package:flutter/material.dart';
import 'package:orderly/presentation/widgets/login_form.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Logo
                Image.asset(
                  'lib/assets/logos/logo_colored.png', // Replace with your asset path
                  height: 100,
                ),
                const SizedBox(height: 24),

                // Encerrar en un contenedor con bordes negros y menos ancho
                Container(
                  width: 400, // Define el ancho máximo del cuadro
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(
                        color: const Color.fromARGB(0, 194, 194, 194),
                        width: 1.0),
                    borderRadius: BorderRadius.circular(
                        4), // Bordes redondeados opcionales
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1), // Sombra ligera
                        spreadRadius: 3,
                        blurRadius: 6,
                        offset:
                            const Offset(0, 0), // Desplazamiento de la sombra
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.all(16.0), // Espaciado interno
                  child: const Column(
                    children: [
                      SizedBox(height: 24),

                      // Title
                      Text(
                        'Login!',
                        style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w200,
                            fontFamily: "Roboto"),
                      ),
                      SizedBox(height: 33),

                      // Username Field
                      LoginForm(),
                      SizedBox(height: 16),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
