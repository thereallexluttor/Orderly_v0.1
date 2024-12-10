import '../entities/user_entity.dart';

abstract class IAuthRepository {
  Future<UserEntity> login(String username, String password);
  Future<List<UserEntity>> getAllUsers();
}
