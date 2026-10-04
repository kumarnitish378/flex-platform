// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mode_setting.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const ModeSettingModeEnum _$modeSettingModeEnum_manual =
    const ModeSettingModeEnum._('manual');
const ModeSettingModeEnum _$modeSettingModeEnum_semiAuto =
    const ModeSettingModeEnum._('semiAuto');
const ModeSettingModeEnum _$modeSettingModeEnum_fullAuto =
    const ModeSettingModeEnum._('fullAuto');

ModeSettingModeEnum _$modeSettingModeEnumValueOf(String name) {
  switch (name) {
    case 'manual':
      return _$modeSettingModeEnum_manual;
    case 'semiAuto':
      return _$modeSettingModeEnum_semiAuto;
    case 'fullAuto':
      return _$modeSettingModeEnum_fullAuto;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ModeSettingModeEnum> _$modeSettingModeEnumValues =
    BuiltSet<ModeSettingModeEnum>(const <ModeSettingModeEnum>[
  _$modeSettingModeEnum_manual,
  _$modeSettingModeEnum_semiAuto,
  _$modeSettingModeEnum_fullAuto,
]);

Serializer<ModeSettingModeEnum> _$modeSettingModeEnumSerializer =
    _$ModeSettingModeEnumSerializer();

class _$ModeSettingModeEnumSerializer
    implements PrimitiveSerializer<ModeSettingModeEnum> {
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
  final Iterable<Type> types = const <Type>[ModeSettingModeEnum];
  @override
  final String wireName = 'ModeSettingModeEnum';

  @override
  Object serialize(Serializers serializers, ModeSettingModeEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ModeSettingModeEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ModeSettingModeEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$ModeSetting extends ModeSetting {
  @override
  final String? id;
  @override
  final String? clientId;
  @override
  final String? zoneId;
  @override
  final Direction? direction;
  @override
  final int? weekdays;
  @override
  final String? startTime;
  @override
  final String? endTime;
  @override
  final ModeSettingModeEnum mode;

  factory _$ModeSetting([void Function(ModeSettingBuilder)? updates]) =>
      (ModeSettingBuilder()..update(updates))._build();

  _$ModeSetting._(
      {this.id,
      this.clientId,
      this.zoneId,
      this.direction,
      this.weekdays,
      this.startTime,
      this.endTime,
      required this.mode})
      : super._();
  @override
  ModeSetting rebuild(void Function(ModeSettingBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ModeSettingBuilder toBuilder() => ModeSettingBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ModeSetting &&
        id == other.id &&
        clientId == other.clientId &&
        zoneId == other.zoneId &&
        direction == other.direction &&
        weekdays == other.weekdays &&
        startTime == other.startTime &&
        endTime == other.endTime &&
        mode == other.mode;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, zoneId.hashCode);
    _$hash = $jc(_$hash, direction.hashCode);
    _$hash = $jc(_$hash, weekdays.hashCode);
    _$hash = $jc(_$hash, startTime.hashCode);
    _$hash = $jc(_$hash, endTime.hashCode);
    _$hash = $jc(_$hash, mode.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ModeSetting')
          ..add('id', id)
          ..add('clientId', clientId)
          ..add('zoneId', zoneId)
          ..add('direction', direction)
          ..add('weekdays', weekdays)
          ..add('startTime', startTime)
          ..add('endTime', endTime)
          ..add('mode', mode))
        .toString();
  }
}

class ModeSettingBuilder implements Builder<ModeSetting, ModeSettingBuilder> {
  _$ModeSetting? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(String? clientId) => _$this._clientId = clientId;

  String? _zoneId;
  String? get zoneId => _$this._zoneId;
  set zoneId(String? zoneId) => _$this._zoneId = zoneId;

  Direction? _direction;
  Direction? get direction => _$this._direction;
  set direction(Direction? direction) => _$this._direction = direction;

  int? _weekdays;
  int? get weekdays => _$this._weekdays;
  set weekdays(int? weekdays) => _$this._weekdays = weekdays;

  String? _startTime;
  String? get startTime => _$this._startTime;
  set startTime(String? startTime) => _$this._startTime = startTime;

  String? _endTime;
  String? get endTime => _$this._endTime;
  set endTime(String? endTime) => _$this._endTime = endTime;

  ModeSettingModeEnum? _mode;
  ModeSettingModeEnum? get mode => _$this._mode;
  set mode(ModeSettingModeEnum? mode) => _$this._mode = mode;

  ModeSettingBuilder() {
    ModeSetting._defaults(this);
  }

  ModeSettingBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _clientId = $v.clientId;
      _zoneId = $v.zoneId;
      _direction = $v.direction;
      _weekdays = $v.weekdays;
      _startTime = $v.startTime;
      _endTime = $v.endTime;
      _mode = $v.mode;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ModeSetting other) {
    _$v = other as _$ModeSetting;
  }

  @override
  void update(void Function(ModeSettingBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ModeSetting build() => _build();

  _$ModeSetting _build() {
    final _$result = _$v ??
        _$ModeSetting._(
          id: id,
          clientId: clientId,
          zoneId: zoneId,
          direction: direction,
          weekdays: weekdays,
          startTime: startTime,
          endTime: endTime,
          mode: BuiltValueNullFieldError.checkNotNull(
              mode, r'ModeSetting', 'mode'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
