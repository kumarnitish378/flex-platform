// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'mode_setting_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const ModeSettingInputModeEnum _$modeSettingInputModeEnum_manual =
    const ModeSettingInputModeEnum._('manual');
const ModeSettingInputModeEnum _$modeSettingInputModeEnum_semiAuto =
    const ModeSettingInputModeEnum._('semiAuto');
const ModeSettingInputModeEnum _$modeSettingInputModeEnum_fullAuto =
    const ModeSettingInputModeEnum._('fullAuto');

ModeSettingInputModeEnum _$modeSettingInputModeEnumValueOf(String name) {
  switch (name) {
    case 'manual':
      return _$modeSettingInputModeEnum_manual;
    case 'semiAuto':
      return _$modeSettingInputModeEnum_semiAuto;
    case 'fullAuto':
      return _$modeSettingInputModeEnum_fullAuto;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ModeSettingInputModeEnum> _$modeSettingInputModeEnumValues =
    BuiltSet<ModeSettingInputModeEnum>(const <ModeSettingInputModeEnum>[
  _$modeSettingInputModeEnum_manual,
  _$modeSettingInputModeEnum_semiAuto,
  _$modeSettingInputModeEnum_fullAuto,
]);

const ModeSettingInputDirectionEnum _$modeSettingInputDirectionEnum_toOffice =
    const ModeSettingInputDirectionEnum._('toOffice');
const ModeSettingInputDirectionEnum _$modeSettingInputDirectionEnum_fromOffice =
    const ModeSettingInputDirectionEnum._('fromOffice');

ModeSettingInputDirectionEnum _$modeSettingInputDirectionEnumValueOf(
    String name) {
  switch (name) {
    case 'toOffice':
      return _$modeSettingInputDirectionEnum_toOffice;
    case 'fromOffice':
      return _$modeSettingInputDirectionEnum_fromOffice;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ModeSettingInputDirectionEnum>
    _$modeSettingInputDirectionEnumValues = BuiltSet<
        ModeSettingInputDirectionEnum>(const <ModeSettingInputDirectionEnum>[
  _$modeSettingInputDirectionEnum_toOffice,
  _$modeSettingInputDirectionEnum_fromOffice,
]);

Serializer<ModeSettingInputModeEnum> _$modeSettingInputModeEnumSerializer =
    _$ModeSettingInputModeEnumSerializer();
Serializer<ModeSettingInputDirectionEnum>
    _$modeSettingInputDirectionEnumSerializer =
    _$ModeSettingInputDirectionEnumSerializer();

class _$ModeSettingInputModeEnumSerializer
    implements PrimitiveSerializer<ModeSettingInputModeEnum> {
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
  final Iterable<Type> types = const <Type>[ModeSettingInputModeEnum];
  @override
  final String wireName = 'ModeSettingInputModeEnum';

  @override
  Object serialize(Serializers serializers, ModeSettingInputModeEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ModeSettingInputModeEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ModeSettingInputModeEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$ModeSettingInputDirectionEnumSerializer
    implements PrimitiveSerializer<ModeSettingInputDirectionEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'toOffice': 'to_office',
    'fromOffice': 'from_office',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'to_office': 'toOffice',
    'from_office': 'fromOffice',
  };

  @override
  final Iterable<Type> types = const <Type>[ModeSettingInputDirectionEnum];
  @override
  final String wireName = 'ModeSettingInputDirectionEnum';

  @override
  Object serialize(
          Serializers serializers, ModeSettingInputDirectionEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ModeSettingInputDirectionEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ModeSettingInputDirectionEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

abstract class ModeSettingInputBuilder {
  void replace(ModeSettingInput other);
  void update(void Function(ModeSettingInputBuilder) updates);
  ModeSettingInputModeEnum? get mode;
  set mode(ModeSettingInputModeEnum? mode);

  String? get clientId;
  set clientId(String? clientId);

  String? get zoneId;
  set zoneId(String? zoneId);

  ModeSettingInputDirectionEnum? get direction;
  set direction(ModeSettingInputDirectionEnum? direction);

  ListBuilder<int> get weekdays;
  set weekdays(ListBuilder<int>? weekdays);

  String? get startTime;
  set startTime(String? startTime);

  String? get endTime;
  set endTime(String? endTime);

  String? get note;
  set note(String? note);
}

class _$$ModeSettingInput extends $ModeSettingInput {
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

  factory _$$ModeSettingInput(
          [void Function($ModeSettingInputBuilder)? updates]) =>
      ($ModeSettingInputBuilder()..update(updates))._build();

  _$$ModeSettingInput._(
      {required this.mode,
      this.clientId,
      this.zoneId,
      this.direction,
      this.weekdays,
      this.startTime,
      this.endTime,
      this.note})
      : super._();
  @override
  $ModeSettingInput rebuild(void Function($ModeSettingInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $ModeSettingInputBuilder toBuilder() =>
      $ModeSettingInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $ModeSettingInput &&
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
    return (newBuiltValueToStringHelper(r'$ModeSettingInput')
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

class $ModeSettingInputBuilder
    implements
        Builder<$ModeSettingInput, $ModeSettingInputBuilder>,
        ModeSettingInputBuilder {
  _$$ModeSettingInput? _$v;

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

  $ModeSettingInputBuilder() {
    $ModeSettingInput._defaults(this);
  }

  $ModeSettingInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
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
  void replace(covariant $ModeSettingInput other) {
    _$v = other as _$$ModeSettingInput;
  }

  @override
  void update(void Function($ModeSettingInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $ModeSettingInput build() => _build();

  _$$ModeSettingInput _build() {
    _$$ModeSettingInput _$result;
    try {
      _$result = _$v ??
          _$$ModeSettingInput._(
            mode: BuiltValueNullFieldError.checkNotNull(
                mode, r'$ModeSettingInput', 'mode'),
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
            r'$ModeSettingInput', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
