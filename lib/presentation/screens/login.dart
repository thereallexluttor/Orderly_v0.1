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

                // Title
                const Text(
                  'Login!',
                  style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w200,
                      fontFamily: "Roboto"),
                ),
                const SizedBox(height: 8),

                // Username Field
                LoginForm(),
                const SizedBox(height: 16),

                // Remember me and Forgot Password

                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
