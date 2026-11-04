// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'device_register.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const DeviceRegisterPlatformEnum _$deviceRegisterPlatformEnum_android =
    const DeviceRegisterPlatformEnum._('android');
const DeviceRegisterPlatformEnum _$deviceRegisterPlatformEnum_ios =
    const DeviceRegisterPlatformEnum._('ios');
const DeviceRegisterPlatformEnum _$deviceRegisterPlatformEnum_web =
    const DeviceRegisterPlatformEnum._('web');

DeviceRegisterPlatformEnum _$deviceRegisterPlatformEnumValueOf(String name) {
  switch (name) {
    case 'android':
      return _$deviceRegisterPlatformEnum_android;
    case 'ios':
      return _$deviceRegisterPlatformEnum_ios;
    case 'web':
      return _$deviceRegisterPlatformEnum_web;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<DeviceRegisterPlatformEnum> _$deviceRegisterPlatformEnumValues =
    BuiltSet<DeviceRegisterPlatformEnum>(const <DeviceRegisterPlatformEnum>[
  _$deviceRegisterPlatformEnum_android,
  _$deviceRegisterPlatformEnum_ios,
  _$deviceRegisterPlatformEnum_web,
]);

Serializer<DeviceRegisterPlatformEnum> _$deviceRegisterPlatformEnumSerializer =
    _$DeviceRegisterPlatformEnumSerializer();

class _$DeviceRegisterPlatformEnumSerializer
    implements PrimitiveSerializer<DeviceRegisterPlatformEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'android': 'android',
    'ios': 'ios',
    'web': 'web',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'android': 'android',
    'ios': 'ios',
    'web': 'web',
  };

  @override
  final Iterable<Type> types = const <Type>[DeviceRegisterPlatformEnum];
  @override
  final String wireName = 'DeviceRegisterPlatformEnum';

  @override
  Object serialize(Serializers serializers, DeviceRegisterPlatformEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  DeviceRegisterPlatformEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      DeviceRegisterPlatformEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$DeviceRegister extends DeviceRegister {
  @override
  final DeviceRegisterPlatformEnum platform;
  @override
  final String pushToken;
  @override
  final String appVersion;

  factory _$DeviceRegister([void Function(DeviceRegisterBuilder)? updates]) =>
      (DeviceRegisterBuilder()..update(updates))._build();

  _$DeviceRegister._(
      {required this.platform,
      required this.pushToken,
      required this.appVersion})
      : super._();
  @override
  DeviceRegister rebuild(void Function(DeviceRegisterBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DeviceRegisterBuilder toBuilder() => DeviceRegisterBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DeviceRegister &&
        platform == other.platform &&
        pushToken == other.pushToken &&
        appVersion == other.appVersion;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, platform.hashCode);
    _$hash = $jc(_$hash, pushToken.hashCode);
    _$hash = $jc(_$hash, appVersion.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DeviceRegister')
          ..add('platform', platform)
          ..add('pushToken', pushToken)
          ..add('appVersion', appVersion))
        .toString();
  }
}

class DeviceRegisterBuilder
    implements Builder<DeviceRegister, DeviceRegisterBuilder> {
  _$DeviceRegister? _$v;

  DeviceRegisterPlatformEnum? _platform;
  DeviceRegisterPlatformEnum? get platform => _$this._platform;
  set platform(DeviceRegisterPlatformEnum? platform) =>
      _$this._platform = platform;

  String? _pushToken;
  String? get pushToken => _$this._pushToken;
  set pushToken(String? pushToken) => _$this._pushToken = pushToken;

  String? _appVersion;
  String? get appVersion => _$this._appVersion;
  set appVersion(String? appVersion) => _$this._appVersion = appVersion;

  DeviceRegisterBuilder() {
    DeviceRegister._defaults(this);
  }

  DeviceRegisterBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _platform = $v.platform;
      _pushToken = $v.pushToken;
      _appVersion = $v.appVersion;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DeviceRegister other) {
    _$v = other as _$DeviceRegister;
  }

  @override
  void update(void Function(DeviceRegisterBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DeviceRegister build() => _build();

  _$DeviceRegister _build() {
    final _$result = _$v ??
        _$DeviceRegister._(
          platform: BuiltValueNullFieldError.checkNotNull(
              platform, r'DeviceRegister', 'platform'),
          pushToken: BuiltValueNullFieldError.checkNotNull(
              pushToken, r'DeviceRegister', 'pushToken'),
          appVersion: BuiltValueNullFieldError.checkNotNull(
              appVersion, r'DeviceRegister', 'appVersion'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
