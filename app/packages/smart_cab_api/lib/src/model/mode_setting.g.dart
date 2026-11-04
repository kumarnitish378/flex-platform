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

const ModeSettingDirectionEnum _$modeSettingDirectionEnum_toOffice =
    const ModeSettingDirectionEnum._('toOffice');
const ModeSettingDirectionEnum _$modeSettingDirectionEnum_fromOffice =
    const ModeSettingDirectionEnum._('fromOffice');

ModeSettingDirectionEnum _$modeSettingDirectionEnumValueOf(String name) {
  switch (name) {
    case 'toOffice':
      return _$modeSettingDirectionEnum_toOffice;
    case 'fromOffice':
      return _$modeSettingDirectionEnum_fromOffice;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ModeSettingDirectionEnum> _$modeSettingDirectionEnumValues =
    BuiltSet<ModeSettingDirectionEnum>(const <ModeSettingDirectionEnum>[
  _$modeSettingDirectionEnum_toOffice,
  _$modeSettingDirectionEnum_fromOffice,
]);

Serializer<ModeSettingModeEnum> _$modeSettingModeEnumSerializer =
    _$ModeSettingModeEnumSerializer();
Serializer<ModeSettingDirectionEnum> _$modeSettingDirectionEnumSerializer =
    _$ModeSettingDirectionEnumSerializer();

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

class _$ModeSettingDirectionEnumSerializer
    implements PrimitiveSerializer<ModeSettingDirectionEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'toOffice': 'to_office',
    'fromOffice': 'from_office',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'to_office': 'toOffice',
    'from_office': 'fromOffice',
  };

  @override
  final Iterable<Type> types = const <Type>[ModeSettingDirectionEnum];
  @override
  final String wireName = 'ModeSettingDirectionEnum';

  @override
  Object serialize(Serializers serializers, ModeSettingDirectionEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ModeSettingDirectionEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ModeSettingDirectionEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$ModeSetting extends ModeSetting {
  @override
  final String? id;
  @override
  final DateTime? updatedAt;
  @override
  final ModeSettingInputModeEnum mode;
  @override
  final String? clientId;
  @override
  final String? zoneId;
  @override
  final ModeSettingInputDirectionEnum? direction;
  @override
  final BuiltList<int>? weekdays;
  @override
  final String? startTime;
  @override
  final String? endTime;
  @override
  final String? note;

  factory _$ModeSetting([void Function(ModeSettingBuilder)? updates]) =>
      (ModeSettingBuilder()..update(updates))._build();

  _$ModeSetting._(
      {this.id,
      this.updatedAt,
      required this.mode,
      this.clientId,
      this.zoneId,
      this.direction,
      this.weekdays,
      this.startTime,
      this.endTime,
      this.note})
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
        updatedAt == other.updatedAt &&
        mode == other.mode &&
        clientId == other.clientId &&
        zoneId == other.zoneId &&
        direction == other.direction &&
        weekdays == other.weekdays &&
        startTime == other.startTime &&
        endTime == other.endTime &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, updatedAt.hashCode);
    _$hash = $jc(_$hash, mode.hashCode);
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, zoneId.hashCode);
    _$hash = $jc(_$hash, direction.hashCode);
    _$hash = $jc(_$hash, weekdays.hashCode);
    _$hash = $jc(_$hash, startTime.hashCode);
    _$hash = $jc(_$hash, endTime.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ModeSetting')
          ..add('id', id)
          ..add('updatedAt', updatedAt)
          ..add('mode', mode)
          ..add('clientId', clientId)
          ..add('zoneId', zoneId)
          ..add('direction', direction)
          ..add('weekdays', weekdays)
          ..add('startTime', startTime)
          ..add('endTime', endTime)
          ..add('note', note))
        .toString();
  }
}

class ModeSettingBuilder
    implements
        Builder<ModeSetting, ModeSettingBuilder>,
        ModeSettingInputBuilder {
  _$ModeSetting? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

  DateTime? _updatedAt;
  DateTime? get updatedAt => _$this._updatedAt;
  set updatedAt(covariant DateTime? updatedAt) => _$this._updatedAt = updatedAt;

  ModeSettingInputModeEnum? _mode;
  ModeSettingInputModeEnum? get mode => _$this._mode;
  set mode(covariant ModeSettingInputModeEnum? mode) => _$this._mode = mode;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(covariant String? clientId) => _$this._clientId = clientId;

  String? _zoneId;
  String? get zoneId => _$this._zoneId;
  set zoneId(covariant String? zoneId) => _$this._zoneId = zoneId;

  ModeSettingInputDirectionEnum? _direction;
  ModeSettingInputDirectionEnum? get direction => _$this._direction;
  set direction(covariant ModeSettingInputDirectionEnum? direction) =>
      _$this._direction = direction;

  ListBuilder<int>? _weekdays;
  ListBuilder<int> get weekdays => _$this._weekdays ??= ListBuilder<int>();
  set weekdays(covariant ListBuilder<int>? weekdays) =>
      _$this._weekdays = weekdays;

  String? _startTime;
  String? get startTime => _$this._startTime;
  set startTime(covariant String? startTime) => _$this._startTime = startTime;

  String? _endTime;
  String? get endTime => _$this._endTime;
  set endTime(covariant String? endTime) => _$this._endTime = endTime;

  String? _note;
  String? get note => _$this._note;
  set note(covariant String? note) => _$this._note = note;

  ModeSettingBuilder() {
    ModeSetting._defaults(this);
  }

  ModeSettingBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _updatedAt = $v.updatedAt;
      _mode = $v.mode;
      _clientId = $v.clientId;
      _zoneId = $v.zoneId;
      _direction = $v.direction;
      _weekdays = $v.weekdays?.toBuilder();
      _startTime = $v.startTime;
      _endTime = $v.endTime;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant ModeSetting other) {
    _$v = other as _$ModeSetting;
  }

  @override
  void update(void Function(ModeSettingBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ModeSetting build() => _build();

  _$ModeSetting _build() {
    _$ModeSetting _$result;
    try {
      _$result = _$v ??
          _$ModeSetting._(
            id: id,
            updatedAt: updatedAt,
            mode: BuiltValueNullFieldError.checkNotNull(
                mode, r'ModeSetting', 'mode'),
            clientId: clientId,
            zoneId: zoneId,
            direction: direction,
            weekdays: _weekdays?.build(),
            startTime: startTime,
            endTime: endTime,
            note: note,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'weekdays';
        _weekdays?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'ModeSetting', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
