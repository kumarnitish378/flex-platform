// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'otp_verify.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OtpVerify extends OtpVerify {
  @override
  final String phone;
  @override
  final String code;

  factory _$OtpVerify([void Function(OtpVerifyBuilder)? updates]) =>
      (OtpVerifyBuilder()..update(updates))._build();

  _$OtpVerify._({required this.phone, required this.code}) : super._();
  @override
  OtpVerify rebuild(void Function(OtpVerifyBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OtpVerifyBuilder toBuilder() => OtpVerifyBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OtpVerify && phone == other.phone && code == other.code;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, phone.hashCode);
    _$hash = $jc(_$hash, code.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OtpVerify')
          ..add('phone', phone)
          ..add('code', code))
        .toString();
  }
}

class OtpVerifyBuilder implements Builder<OtpVerify, OtpVerifyBuilder> {
  _$OtpVerify? _$v;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(String? phone) => _$this._phone = phone;

  String? _code;
  String? get code => _$this._code;
  set code(String? code) => _$this._code = code;

  OtpVerifyBuilder() {
    OtpVerify._defaults(this);
  }

  OtpVerifyBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _phone = $v.phone;
      _code = $v.code;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OtpVerify other) {
    _$v = other as _$OtpVerify;
  }

  @override
  void update(void Function(OtpVerifyBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OtpVerify build() => _build();

  _$OtpVerify _build() {
    final _$result = _$v ??
        _$OtpVerify._(
          phone: BuiltValueNullFieldError.checkNotNull(
              phone, r'OtpVerify', 'phone'),
          code:
              BuiltValueNullFieldError.checkNotNull(code, r'OtpVerify', 'code'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
