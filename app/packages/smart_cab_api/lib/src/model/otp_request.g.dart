// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'otp_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OtpRequest extends OtpRequest {
  @override
  final String phone;

  factory _$OtpRequest([void Function(OtpRequestBuilder)? updates]) =>
      (OtpRequestBuilder()..update(updates))._build();

  _$OtpRequest._({required this.phone}) : super._();
  @override
  OtpRequest rebuild(void Function(OtpRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OtpRequestBuilder toBuilder() => OtpRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OtpRequest && phone == other.phone;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, phone.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OtpRequest')..add('phone', phone))
        .toString();
  }
}

class OtpRequestBuilder implements Builder<OtpRequest, OtpRequestBuilder> {
  _$OtpRequest? _$v;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(String? phone) => _$this._phone = phone;

  OtpRequestBuilder() {
    OtpRequest._defaults(this);
  }

  OtpRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _phone = $v.phone;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OtpRequest other) {
    _$v = other as _$OtpRequest;
  }

  @override
  void update(void Function(OtpRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OtpRequest build() => _build();

  _$OtpRequest _build() {
    final _$result = _$v ??
        _$OtpRequest._(
          phone: BuiltValueNullFieldError.checkNotNull(
              phone, r'OtpRequest', 'phone'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
