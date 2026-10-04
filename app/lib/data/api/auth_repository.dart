/// The auth calls, wrapped so screens never touch the generated client (A03).
///
/// `coding-standards.md` section 3 rule 3: the API is reached only through the generated
/// client, wrapped in repositories. This is that wrapper for `/auth/*`.
///
/// The shape of the backend's answers matters here and is worth stating, because it is
/// deliberate and it looks like a bug if you do not know (B03, OQ-24):
///
/// * `POST /auth/otp/request` answers **202 for any well-formed phone**, whether or not
///   it belongs to anybody. A 404 would turn the endpoint into a directory of an
///   operator's staff and riders. So the app cannot - and must not try to - tell the
///   caller whether their number is registered.
/// * `POST /auth/otp/verify` answers **one indistinguishable error** for a wrong code, an
///   expired code, a code for an unknown number, and a locked-out account. The app shows
///   one message for all of them, because distinguishing them tells an attacker which
///   half of the guess was right.
library;

import 'package:dio/dio.dart';
// Aliased: the generated client has its own `Role`, and so does the app. They are not
// the same type - the generated one is a built_value `EnumClass` whose `name` is the
// Dart spelling (`platformAdmin`), while ours carries the wire spelling that goes in
// `X-Active-Role`. Keeping both visible unaliased is how the wrong one gets sent.
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session.dart';

/// What `/auth/me` says about who this is.
class Identity {
  const Identity({required this.userId, required this.name, required this.roles});

  final String userId;
  final String name;

  /// Every role this person holds, in the order the server returned them.
  final List<Role> roles;
}

/// Raised when the OTP could not be verified.
///
/// Carries no detail on purpose: there is none to carry. See the note above.
class OtpRejected implements Exception {
  const OtpRejected();
}

/// Raised when the request could not reach the backend at all.
///
/// Separate from [OtpRejected] because the two need different words on screen: "that
/// code did not work" is the user's problem to fix, "we could not reach the server" is
/// not, and telling someone to re-check a correct code is maddening.
class AuthUnavailable implements Exception {
  const AuthUnavailable(this.cause);

  final String cause;
}

class AuthRepository {
  AuthRepository(this._api);

  final api.AuthApi _api;

  /// Ask for a code. Succeeds for any well-formed number; see the note above.
  Future<void> requestCode(String phone) async {
    try {
      await _api.authOtpRequestPost(
        otpRequest: api.OtpRequest((api.OtpRequestBuilder builder) => builder.phone = phone),
      );
    } on DioException catch (error) {
      if (error.response?.statusCode == 429) {
        // Rate limited. Worth surfacing as itself: the honest message is "wait a
        // moment", and showing "could not reach the server" would be a lie.
        throw const AuthUnavailable('too_many_requests');
      }
      throw AuthUnavailable(error.type.name);
    }
  }

  /// Exchange a code for tokens.
  Future<api.TokenPair> verifyCode({required String phone, required String code}) async {
    try {
      final Response<api.TokenPair> response = await _api.authOtpVerifyPost(
        otpVerify: api.OtpVerify(
          (api.OtpVerifyBuilder builder) => builder
            ..phone = phone
            ..code = code,
        ),
      );
      final api.TokenPair? pair = response.data;
      if (pair == null) {
        throw const AuthUnavailable('empty_response');
      }
      return pair;
    } on DioException catch (error) {
      final int? status = error.response?.statusCode;
      if (status == 401 || status == 422) {
        throw const OtpRejected();
      }
      throw AuthUnavailable(error.type.name);
    }
  }

  /// Rotate the token pair. `null` when the session cannot be recovered.
  Future<api.TokenPair?> refresh(String refreshToken) async {
    try {
      final Response<api.TokenPair> response = await _api.authRefreshPost(
        authRefreshPostRequest: api.AuthRefreshPostRequest(
          (api.AuthRefreshPostRequestBuilder builder) => builder.refreshToken = refreshToken,
        ),
      );
      return response.data;
    } on DioException {
      // Any failure here means "sign in again". Distinguishing a revoked token from an
      // unreachable server would be nice and is not worth a retry loop on the one call
      // that runs while the app is starting.
      return null;
    }
  }

  /// Who this is, and which roles they hold. Drives navigation (C-01, C-03).
  Future<Identity?> me() async {
    try {
      final api.Me? body = (await _api.authMeGet()).data;
      if (body == null) {
        return null;
      }
      final List<Role> roles = <Role>[
        for (final api.MeRolesInner entry in body.roles ?? <api.MeRolesInner>[])
          if (_roleFrom(entry.role) case final Role role) role,
      ];
      return Identity(
        userId: body.userId ?? '',
        name: body.name ?? '',
        roles: roles,
      );
    } on DioException {
      return null;
    }
  }

  /// Revoke the refresh token server-side. Best effort.
  ///
  /// A sign-out that fails must still clear the device: the person asked to be signed
  /// out, and leaving the tokens in storage because the network was down is the opposite
  /// of what they wanted. The server's copy expires on its own.
  Future<void> logout() async {
    try {
      await _api.authLogoutPost();
    } on DioException {
      return;
    }
  }
}


/// The generated enum to ours.
///
/// Written out rather than matched on `name`: the generated `name` is `platformAdmin`
/// while the wire value is `platform_admin`, so a string round-trip through `name` would
/// silently map nothing and leave a signed-in person with no roles at all. `null` for an
/// unknown value, so a role the app does not understand is ignored rather than crashing
/// the whole sign-in.
Role? _roleFrom(api.Role? role) {
  return switch (role) {
    api.Role.platformAdmin => Role.platformAdmin,
    api.Role.operatorAdmin => Role.operatorAdmin,
    api.Role.supervisor => Role.supervisor,
    api.Role.driver => Role.driver,
    api.Role.clientAdmin => Role.clientAdmin,
    api.Role.employee => Role.employee,
    _ => null,
  };
}
