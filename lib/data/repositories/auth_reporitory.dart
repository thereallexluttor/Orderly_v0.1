import 'package:supabase_flutter/supabase_flutter.dart';
import '../../domain/repositories/i_auth_repository.dart';
import '../models/user_model.dart';

class AuthRepository implements IAuthRepository {
  final SupabaseClient _supabase;

  AuthRepository(this._supabase);

  @override
  Future<UserModel> login(String username, String password) async {
    final user = await _supabase
        .from('user_table')
        .select()
        .eq('user_id', username)
        .eq('user_pswrd', password)
        .single();

    return UserModel.fromJson(user);
  }

  @override
  Future<List<UserModel>> getAllUsers() async {
    final users = await _supabase.from('user_table').select();
    return users.map((user) => UserModel.fromJson(user)).toList();
  }
}
