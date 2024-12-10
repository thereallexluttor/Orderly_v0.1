import '../../domain/repositories/i_auth_repository.dart';

class LoginController {
  final IAuthRepository _authRepository;

  LoginController(this._authRepository);

  Future<void> login(String username, String password) async {
    if (username.isEmpty || password.isEmpty) {
      throw 'Please fill in all fields';
    }

    await _authRepository.login(username, password);
  }
}
