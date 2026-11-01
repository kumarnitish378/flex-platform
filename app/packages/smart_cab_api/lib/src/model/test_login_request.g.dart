// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'test_login_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$TestLoginRequest extends TestLoginRequest {
  @override
  final String phone;

  factory _$TestLoginRequest(
          [void Function(TestLoginRequestBuilder)? updates]) =>
      (TestLoginRequestBuilder()..update(updates))._build();

  _$TestLoginRequest._({required this.phone}) : super._();
  @override
  TestLoginRequest rebuild(void Function(TestLoginRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TestLoginRequestBuilder toBuilder() =>
      TestLoginRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is TestLoginRequest && phone == other.phone;
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
    return (newBuiltValueToStringHelper(r'TestLoginRequest')
          ..add('phone', phone))
        .toString();
  }
}

class TestLoginRequestBuilder
    implements Builder<TestLoginRequest, TestLoginRequestBuilder> {
  _$TestLoginRequest? _$v;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(String? phone) => _$this._phone = phone;

  TestLoginRequestBuilder() {
    TestLoginRequest._defaults(this);
  }

  TestLoginRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _phone = $v.phone;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(TestLoginRequest other) {
    _$v = other as _$TestLoginRequest;
  }

  @override
  void update(void Function(TestLoginRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  TestLoginRequest build() => _build();

  _$TestLoginRequest _build() {
    final _$result = _$v ??
        _$TestLoginRequest._(
          phone: BuiltValueNullFieldError.checkNotNull(
              phone, r'TestLoginRequest', 'phone'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
