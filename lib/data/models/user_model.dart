import '../../domain/entities/user_entity.dart';

class UserModel extends UserEntity {
  UserModel({
    required super.userId,
    required super.password,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      userId: json['user_id'],
      password: json['user_pswrd'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'user_pswrd': password,
    };
  }
}
