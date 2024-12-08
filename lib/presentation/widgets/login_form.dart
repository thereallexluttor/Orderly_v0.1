import 'package:flutter/material.dart';

class LoginForm extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Username Field
        TextFormField(
          decoration: InputDecoration(
            labelText: 'Username',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        const SizedBox(height: 16),

        // Password Field
        TextFormField(
          obscureText: true,
          decoration: InputDecoration(
            labelText: 'Password',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
            suffixIcon: Icon(Icons.visibility),
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
                  value: false,
                  onChanged: (value) {},
                ),
                const Text('Remember me'),
              ],
            ),
            TextButton(
              onPressed: () {},
              child: const Text('Forgot Password?'),
            ),
          ],
        ),

        const SizedBox(height: 24),

        // Login Button
        ElevatedButton(
          onPressed: () {
            // Implement login logic here
            print('Login button pressed');
          },
          style: ElevatedButton.styleFrom(
            minimumSize: const Size(double.infinity, 50),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: const Text('Login'),
        ),
      ],
    );
  }
}
