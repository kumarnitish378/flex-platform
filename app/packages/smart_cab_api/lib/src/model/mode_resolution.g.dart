// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mode_resolution.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const ModeResolutionModeEnum _$modeResolutionModeEnum_manual =
    const ModeResolutionModeEnum._('manual');
const ModeResolutionModeEnum _$modeResolutionModeEnum_semiAuto =
    const ModeResolutionModeEnum._('semiAuto');
const ModeResolutionModeEnum _$modeResolutionModeEnum_fullAuto =
    const ModeResolutionModeEnum._('fullAuto');

ModeResolutionModeEnum _$modeResolutionModeEnumValueOf(String name) {
  switch (name) {
    case 'manual':
      return _$modeResolutionModeEnum_manual;
    case 'semiAuto':
      return _$modeResolutionModeEnum_semiAuto;
    case 'fullAuto':
      return _$modeResolutionModeEnum_fullAuto;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ModeResolutionModeEnum> _$modeResolutionModeEnumValues =
    BuiltSet<ModeResolutionModeEnum>(const <ModeResolutionModeEnum>[
  _$modeResolutionModeEnum_manual,
  _$modeResolutionModeEnum_semiAuto,
  _$modeResolutionModeEnum_fullAuto,
]);

const ModeResolutionReasonEnum _$modeResolutionReasonEnum_automationPaused =
    const ModeResolutionReasonEnum._('automationPaused');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_vip =
    const ModeResolutionReasonEnum._('vip');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_clientZoneTime =
    const ModeResolutionReasonEnum._('clientZoneTime');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_clientTime =
    const ModeResolutionReasonEnum._('clientTime');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_zoneTime =
    const ModeResolutionReasonEnum._('zoneTime');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_clientZone =
    const ModeResolutionReasonEnum._('clientZone');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_client =
    const ModeResolutionReasonEnum._('client');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_zone =
    const ModeResolutionReasonEnum._('zone');
const ModeResolutionReasonEnum _$modeResolutionReasonEnum_operatorDefault =
    const ModeResolutionReasonEnum._('operatorDefault');

ModeResolutionReasonEnum _$modeResolutionReasonEnumValueOf(String name) {
  switch (name) {
    case 'automationPaused':
      return _$modeResolutionReasonEnum_automationPaused;
    case 'vip':
      return _$modeResolutionReasonEnum_vip;
    case 'clientZoneTime':
      return _$modeResolutionReasonEnum_clientZoneTime;
    case 'clientTime':
      return _$modeResolutionReasonEnum_clientTime;
    case 'zoneTime':
      return _$modeResolutionReasonEnum_zoneTime;
    case 'clientZone':
      return _$modeResolutionReasonEnum_clientZone;
    case 'client':
      return _$modeResolutionReasonEnum_client;
    case 'zone':
      return _$modeResolutionReasonEnum_zone;
    case 'operatorDefault':
      return _$modeResolutionReasonEnum_operatorDefault;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ModeResolutionReasonEnum> _$modeResolutionReasonEnumValues =
    BuiltSet<ModeResolutionReasonEnum>(const <ModeResolutionReasonEnum>[
  _$modeResolutionReasonEnum_automationPaused,
  _$modeResolutionReasonEnum_vip,
  _$modeResolutionReasonEnum_clientZoneTime,
  _$modeResolutionReasonEnum_clientTime,
  _$modeResolutionReasonEnum_zoneTime,
  _$modeResolutionReasonEnum_clientZone,
  _$modeResolutionReasonEnum_client,
  _$modeResolutionReasonEnum_zone,
  _$modeResolutionReasonEnum_operatorDefault,
]);

Serializer<ModeResolutionModeEnum> _$modeResolutionModeEnumSerializer =
    _$ModeResolutionModeEnumSerializer();
Serializer<ModeResolutionReasonEnum> _$modeResolutionReasonEnumSerializer =
    _$ModeResolutionReasonEnumSerializer();

class _$ModeResolutionModeEnumSerializer
    implements PrimitiveSerializer<ModeResolutionModeEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'manual': 'manual',
    'semiAuto': 'semi_auto',
    'fullAuto': 'full_auto',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'manual': 'manual',
    'semi_auto': 'semiAuto',
    'full_auto': 'fullAuto',
  };

  @override
  final Iterable<Type> types = const <Type>[ModeResolutionModeEnum];
  @override
  final String wireName = 'ModeResolutionModeEnum';

  @override
  Object serialize(Serializers serializers, ModeResolutionModeEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ModeResolutionModeEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ModeResolutionModeEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$ModeResolutionReasonEnumSerializer
    implements PrimitiveSerializer<ModeResolutionReasonEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'automationPaused': 'automation_paused',
    'vip': 'vip',
    'clientZoneTime': 'client_zone_time',
    'clientTime': 'client_time',
    'zoneTime': 'zone_time',
    'clientZone': 'client_zone',
    'client': 'client',
    'zone': 'zone',
    'operatorDefault': 'operator_default',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'automation_paused': 'automationPaused',
    'vip': 'vip',
    'client_zone_time': 'clientZoneTime',
    'client_time': 'clientTime',
    'zone_time': 'zoneTime',
    'client_zone': 'clientZone',
    'client': 'client',
    'zone': 'zone',
    'operator_default': 'operatorDefault',
  };

  @override
  final Iterable<Type> types = const <Type>[ModeResolutionReasonEnum];
  @override
  final String wireName = 'ModeResolutionReasonEnum';

  @override
  Object serialize(Serializers serializers, ModeResolutionReasonEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ModeResolutionReasonEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ModeResolutionReasonEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$ModeResolution extends ModeResolution {
  @override
  final ModeResolutionModeEnum? mode;
  @override
  final ModeResolutionReasonEnum? reason;
  @override
  final String? settingId;

  factory _$ModeResolution([void Function(ModeResolutionBuilder)? updates]) =>
      (ModeResolutionBuilder()..update(updates))._build();

  _$ModeResolution._({this.mode, this.reason, this.settingId}) : super._();
  @override
  ModeResolution rebuild(void Function(ModeResolutionBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ModeResolutionBuilder toBuilder() => ModeResolutionBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ModeResolution &&
        mode == other.mode &&
        reason == other.reason &&
        settingId == other.settingId;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, mode.hashCode);
    _$hash = $jc(_$hash, reason.hashCode);
    _$hash = $jc(_$hash, settingId.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ModeResolution')
          ..add('mode', mode)
          ..add('reason', reason)
          ..add('settingId', settingId))
        .toString();
  }
}

class ModeResolutionBuilder
    implements Builder<ModeResolution, ModeResolutionBuilder> {
  _$ModeResolution? _$v;

  ModeResolutionModeEnum? _mode;
  ModeResolutionModeEnum? get mode => _$this._mode;
  set mode(ModeResolutionModeEnum? mode) => _$this._mode = mode;

  ModeResolutionReasonEnum? _reason;
  ModeResolutionReasonEnum? get reason => _$this._reason;
  set reason(ModeResolutionReasonEnum? reason) => _$this._reason = reason;

  String? _settingId;
  String? get settingId => _$this._settingId;
  set settingId(String? settingId) => _$this._settingId = settingId;

  ModeResolutionBuilder() {
    ModeResolution._defaults(this);
  }

  ModeResolutionBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _mode = $v.mode;
      _reason = $v.reason;
      _settingId = $v.settingId;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ModeResolution other) {
    _$v = other as _$ModeResolution;
  }

  @override
  void update(void Function(ModeResolutionBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ModeResolution build() => _build();

  _$ModeResolution _build() {
    final _$result = _$v ??
        _$ModeResolution._(
          mode: mode,
          reason: reason,
          settingId: settingId,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
