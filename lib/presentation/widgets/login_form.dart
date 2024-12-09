import 'package:flutter/material.dart';

class LoginForm extends StatefulWidget {
  const LoginForm({super.key});

  @override
  LoginFormState createState() => LoginFormState();
}

class LoginFormState extends State<LoginForm> {
  bool _obscureText = true;
  bool _rememberMe = false;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 450),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Username Field
            TextFormField(
              decoration: const InputDecoration(
                labelText: 'Username',
                labelStyle: TextStyle(
                  fontFamily: 'Roboto',
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
            const SizedBox(height: 33),

            // Password Field
            TextFormField(
              obscureText: _obscureText,
              decoration: InputDecoration(
                labelText: 'Password',
                labelStyle: const TextStyle(
                  fontFamily: 'Roboto',
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
                    _obscureText ? Icons.visibility : Icons.visibility_off,
                  ),
                  onPressed: () {
                    setState(() {
                      _obscureText = !_obscureText;
                    });
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Remember me and Forgot Password
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Checkbox(
                      value: _rememberMe,
                      onChanged: (value) {
                        setState(() {
                          _rememberMe = value!;
                        });
                      },
                    ),
                    const Text(
                      'Remember me',
                      style: TextStyle(fontWeight: FontWeight.w300),
                    ),
                  ],
                ),
                TextButton(
                  onPressed: () {},
                  child: const Text(
                    'Forgot Password?',
                    style: TextStyle(fontWeight: FontWeight.w300),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // Login Button with Animation
            AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeInOut,
              child: ElevatedButton(
                onPressed: () {
                  // Implement login logic here
                  print('Login button pressed');
                },
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
                child: const Text(
                  'Login',
                  style: TextStyle(
                    color: Colors.black,
                    fontWeight: FontWeight.w300,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
