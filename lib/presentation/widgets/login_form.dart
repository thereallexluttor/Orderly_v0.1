import 'package:flutter/material.dart';
import '../controllers/login_controller.dart';
import '../screens/homepage.dart';

class LoginForm extends StatefulWidget {
  final LoginController controller;

  const LoginForm({
    required this.controller,
    super.key,
  });

  @override
  LoginFormState createState() => LoginFormState();
}

class LoginFormState extends State<LoginForm> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscureText = true;
  bool _isLoading = false;

  Future<void> _handleLogin() async {
    setState(() => _isLoading = true);

    try {
      await widget.controller.login(
        _usernameController.text,
        _passwordController.text,
      );

      if (mounted) {
        Navigator.of(context).pushNamedAndRemoveUntil(
          HomePage.routeName,
          (route) => false,
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Login failed')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 450),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            TextFormField(
              controller: _usernameController,
              decoration: const InputDecoration(
                labelText: 'Username',
                labelStyle: TextStyle(
                  color: Colors.grey,
                  fontWeight: FontWeight.normal,
                ),
                border: OutlineInputBorder(
                  borderSide:
                      BorderSide(color: Color.fromARGB(255, 128, 128, 128)),
                  borderRadius: BorderRadius.all(Radius.circular(4)),
                ),
              ),
            ),
            const SizedBox(height: 23),

            TextFormField(
              controller: _passwordController,
              obscureText: _obscureText,
              decoration: InputDecoration(
                labelText: 'Password',
                labelStyle: const TextStyle(
                  color: Colors.grey,
                  fontWeight: FontWeight.w300,
                ),
                border: const OutlineInputBorder(
                  borderSide:
                      BorderSide(color: Color.fromARGB(255, 128, 128, 128)),
                  borderRadius: BorderRadius.all(Radius.circular(4)),
                ),
                suffixIcon: IconButton(
                  icon: Icon(
                      _obscureText ? Icons.visibility : Icons.visibility_off),
                  onPressed: () => setState(() => _obscureText = !_obscureText),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Login Button
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeInOut,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handleLogin,
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(100, 50),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(4),
                    side: const BorderSide(
                      color: Color.fromARGB(255, 199, 199, 199),
                      width: 1.0,
                    ),
                  ),
                  backgroundColor: Colors.white,
                ),
                child: _isLoading
                    ? const CircularProgressIndicator()
                    : const Text(
                        'Login',
                        style: TextStyle(
                          color: Colors.black,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}
