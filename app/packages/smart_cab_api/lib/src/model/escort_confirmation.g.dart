// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'escort_confirmation.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const EscortConfirmationBasisEnum _$escortConfirmationBasisEnum_escortArranged =
    const EscortConfirmationBasisEnum._('escortArranged');
const EscortConfirmationBasisEnum
    _$escortConfirmationBasisEnum_maleCoRiderPresent =
    const EscortConfirmationBasisEnum._('maleCoRiderPresent');

EscortConfirmationBasisEnum _$escortConfirmationBasisEnumValueOf(String name) {
  switch (name) {
    case 'escortArranged':
      return _$escortConfirmationBasisEnum_escortArranged;
    case 'maleCoRiderPresent':
      return _$escortConfirmationBasisEnum_maleCoRiderPresent;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<EscortConfirmationBasisEnum>
    _$escortConfirmationBasisEnumValues =
    BuiltSet<EscortConfirmationBasisEnum>(const <EscortConfirmationBasisEnum>[
  _$escortConfirmationBasisEnum_escortArranged,
  _$escortConfirmationBasisEnum_maleCoRiderPresent,
]);

Serializer<EscortConfirmationBasisEnum>
    _$escortConfirmationBasisEnumSerializer =
    _$EscortConfirmationBasisEnumSerializer();

class _$EscortConfirmationBasisEnumSerializer
    implements PrimitiveSerializer<EscortConfirmationBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'escortArranged': 'escort_arranged',
    'maleCoRiderPresent': 'male_co_rider_present',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'escort_arranged': 'escortArranged',
    'male_co_rider_present': 'maleCoRiderPresent',
  };

  @override
  final Iterable<Type> types = const <Type>[EscortConfirmationBasisEnum];
  @override
  final String wireName = 'EscortConfirmationBasisEnum';

  @override
  Object serialize(Serializers serializers, EscortConfirmationBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  EscortConfirmationBasisEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      EscortConfirmationBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$EscortConfirmation extends EscortConfirmation {
  @override
  final EscortConfirmationBasisEnum basis;
  @override
  final String? note;

  factory _$EscortConfirmation(
          [void Function(EscortConfirmationBuilder)? updates]) =>
      (EscortConfirmationBuilder()..update(updates))._build();

  _$EscortConfirmation._({required this.basis, this.note}) : super._();
  @override
  EscortConfirmation rebuild(
          void Function(EscortConfirmationBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  EscortConfirmationBuilder toBuilder() =>
      EscortConfirmationBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is EscortConfirmation &&
        basis == other.basis &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, basis.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'EscortConfirmation')
          ..add('basis', basis)
          ..add('note', note))
        .toString();
  }
}

class EscortConfirmationBuilder
    implements Builder<EscortConfirmation, EscortConfirmationBuilder> {
  _$EscortConfirmation? _$v;

  EscortConfirmationBasisEnum? _basis;
  EscortConfirmationBasisEnum? get basis => _$this._basis;
  set basis(EscortConfirmationBasisEnum? basis) => _$this._basis = basis;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  EscortConfirmationBuilder() {
    EscortConfirmation._defaults(this);
  }

  EscortConfirmationBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _basis = $v.basis;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(EscortConfirmation other) {
    _$v = other as _$EscortConfirmation;
  }

  @override
  void update(void Function(EscortConfirmationBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  EscortConfirmation build() => _build();

  _$EscortConfirmation _build() {
    final _$result = _$v ??
        _$EscortConfirmation._(
          basis: BuiltValueNullFieldError.checkNotNull(
              basis, r'EscortConfirmation', 'basis'),
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
