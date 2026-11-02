// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trip_escort.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const TripEscortBasisEnum _$tripEscortBasisEnum_escortArranged =
    const TripEscortBasisEnum._('escortArranged');
const TripEscortBasisEnum _$tripEscortBasisEnum_maleCoRiderPresent =
    const TripEscortBasisEnum._('maleCoRiderPresent');

TripEscortBasisEnum _$tripEscortBasisEnumValueOf(String name) {
  switch (name) {
    case 'escortArranged':
      return _$tripEscortBasisEnum_escortArranged;
    case 'maleCoRiderPresent':
      return _$tripEscortBasisEnum_maleCoRiderPresent;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<TripEscortBasisEnum> _$tripEscortBasisEnumValues =
    BuiltSet<TripEscortBasisEnum>(const <TripEscortBasisEnum>[
  _$tripEscortBasisEnum_escortArranged,
  _$tripEscortBasisEnum_maleCoRiderPresent,
]);

Serializer<TripEscortBasisEnum> _$tripEscortBasisEnumSerializer =
    _$TripEscortBasisEnumSerializer();

class _$TripEscortBasisEnumSerializer
    implements PrimitiveSerializer<TripEscortBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'escortArranged': 'escort_arranged',
    'maleCoRiderPresent': 'male_co_rider_present',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'escort_arranged': 'escortArranged',
    'male_co_rider_present': 'maleCoRiderPresent',
  };

  @override
  final Iterable<Type> types = const <Type>[TripEscortBasisEnum];
  @override
  final String wireName = 'TripEscortBasisEnum';

  @override
  Object serialize(Serializers serializers, TripEscortBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  TripEscortBasisEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      TripEscortBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$TripEscort extends TripEscort {
  @override
  final bool required_;
  @override
  final bool confirmed;
  @override
  final TripEscortBasisEnum? basis;
  @override
  final String? confirmedBy;
  @override
  final DateTime? confirmedAt;
  @override
  final String? note;

  factory _$TripEscort([void Function(TripEscortBuilder)? updates]) =>
      (TripEscortBuilder()..update(updates))._build();

  _$TripEscort._(
      {required this.required_,
      required this.confirmed,
      this.basis,
      this.confirmedBy,
      this.confirmedAt,
      this.note})
      : super._();
  @override
  TripEscort rebuild(void Function(TripEscortBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TripEscortBuilder toBuilder() => TripEscortBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is TripEscort &&
        required_ == other.required_ &&
        confirmed == other.confirmed &&
        basis == other.basis &&
        confirmedBy == other.confirmedBy &&
        confirmedAt == other.confirmedAt &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, required_.hashCode);
    _$hash = $jc(_$hash, confirmed.hashCode);
    _$hash = $jc(_$hash, basis.hashCode);
    _$hash = $jc(_$hash, confirmedBy.hashCode);
    _$hash = $jc(_$hash, confirmedAt.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'TripEscort')
          ..add('required_', required_)
          ..add('confirmed', confirmed)
          ..add('basis', basis)
          ..add('confirmedBy', confirmedBy)
          ..add('confirmedAt', confirmedAt)
          ..add('note', note))
        .toString();
  }
}

class TripEscortBuilder implements Builder<TripEscort, TripEscortBuilder> {
  _$TripEscort? _$v;

  bool? _required_;
  bool? get required_ => _$this._required_;
  set required_(bool? required_) => _$this._required_ = required_;

  bool? _confirmed;
  bool? get confirmed => _$this._confirmed;
  set confirmed(bool? confirmed) => _$this._confirmed = confirmed;

  TripEscortBasisEnum? _basis;
  TripEscortBasisEnum? get basis => _$this._basis;
  set basis(TripEscortBasisEnum? basis) => _$this._basis = basis;

  String? _confirmedBy;
  String? get confirmedBy => _$this._confirmedBy;
  set confirmedBy(String? confirmedBy) => _$this._confirmedBy = confirmedBy;

  DateTime? _confirmedAt;
  DateTime? get confirmedAt => _$this._confirmedAt;
  set confirmedAt(DateTime? confirmedAt) => _$this._confirmedAt = confirmedAt;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  TripEscortBuilder() {
    TripEscort._defaults(this);
  }

  TripEscortBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _required_ = $v.required_;
      _confirmed = $v.confirmed;
      _basis = $v.basis;
      _confirmedBy = $v.confirmedBy;
      _confirmedAt = $v.confirmedAt;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(TripEscort other) {
    _$v = other as _$TripEscort;
  }

  @override
  void update(void Function(TripEscortBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  TripEscort build() => _build();

  _$TripEscort _build() {
    final _$result = _$v ??
        _$TripEscort._(
          required_: BuiltValueNullFieldError.checkNotNull(
              required_, r'TripEscort', 'required_'),
          confirmed: BuiltValueNullFieldError.checkNotNull(
              confirmed, r'TripEscort', 'confirmed'),
          basis: basis,
          confirmedBy: confirmedBy,
          confirmedAt: confirmedAt,
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
