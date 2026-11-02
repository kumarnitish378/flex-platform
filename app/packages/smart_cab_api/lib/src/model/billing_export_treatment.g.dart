// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_treatment.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const BillingExportTreatmentDistanceBasisEnum
    _$billingExportTreatmentDistanceBasisEnum_tripShare =
    const BillingExportTreatmentDistanceBasisEnum._('tripShare');
const BillingExportTreatmentDistanceBasisEnum
    _$billingExportTreatmentDistanceBasisEnum_direct =
    const BillingExportTreatmentDistanceBasisEnum._('direct');

BillingExportTreatmentDistanceBasisEnum
    _$billingExportTreatmentDistanceBasisEnumValueOf(String name) {
  switch (name) {
    case 'tripShare':
      return _$billingExportTreatmentDistanceBasisEnum_tripShare;
    case 'direct':
      return _$billingExportTreatmentDistanceBasisEnum_direct;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<BillingExportTreatmentDistanceBasisEnum>
    _$billingExportTreatmentDistanceBasisEnumValues = BuiltSet<
        BillingExportTreatmentDistanceBasisEnum>(const <BillingExportTreatmentDistanceBasisEnum>[
  _$billingExportTreatmentDistanceBasisEnum_tripShare,
  _$billingExportTreatmentDistanceBasisEnum_direct,
]);

const BillingExportTreatmentBasisEnum _$billingExportTreatmentBasisEnum_perKm =
    const BillingExportTreatmentBasisEnum._('perKm');

BillingExportTreatmentBasisEnum _$billingExportTreatmentBasisEnumValueOf(
    String name) {
  switch (name) {
    case 'perKm':
      return _$billingExportTreatmentBasisEnum_perKm;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<BillingExportTreatmentBasisEnum>
    _$billingExportTreatmentBasisEnumValues = BuiltSet<
        BillingExportTreatmentBasisEnum>(const <BillingExportTreatmentBasisEnum>[
  _$billingExportTreatmentBasisEnum_perKm,
]);

Serializer<BillingExportTreatmentDistanceBasisEnum>
    _$billingExportTreatmentDistanceBasisEnumSerializer =
    _$BillingExportTreatmentDistanceBasisEnumSerializer();
Serializer<BillingExportTreatmentBasisEnum>
    _$billingExportTreatmentBasisEnumSerializer =
    _$BillingExportTreatmentBasisEnumSerializer();

class _$BillingExportTreatmentDistanceBasisEnumSerializer
    implements PrimitiveSerializer<BillingExportTreatmentDistanceBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'tripShare': 'trip_share',
    'direct': 'direct',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'trip_share': 'tripShare',
    'direct': 'direct',
  };

  @override
  final Iterable<Type> types = const <Type>[
    BillingExportTreatmentDistanceBasisEnum
  ];
  @override
  final String wireName = 'BillingExportTreatmentDistanceBasisEnum';

  @override
  Object serialize(Serializers serializers,
          BillingExportTreatmentDistanceBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  BillingExportTreatmentDistanceBasisEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      BillingExportTreatmentDistanceBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$BillingExportTreatmentBasisEnumSerializer
    implements PrimitiveSerializer<BillingExportTreatmentBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'perKm': 'per_km',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'per_km': 'perKm',
  };

  @override
  final Iterable<Type> types = const <Type>[BillingExportTreatmentBasisEnum];
  @override
  final String wireName = 'BillingExportTreatmentBasisEnum';

  @override
  Object serialize(
          Serializers serializers, BillingExportTreatmentBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  BillingExportTreatmentBasisEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      BillingExportTreatmentBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$BillingExportTreatment extends BillingExportTreatment {
  @override
  final bool? noShowBillable;
  @override
  final bool? lateCancelBillable;
  @override
  final BillingExportTreatmentDistanceBasisEnum? distanceBasis;
  @override
  final BillingExportTreatmentBasisEnum? basis;
  @override
  final num? ratePerKm;

  factory _$BillingExportTreatment(
          [void Function(BillingExportTreatmentBuilder)? updates]) =>
      (BillingExportTreatmentBuilder()..update(updates))._build();

  _$BillingExportTreatment._(
      {this.noShowBillable,
      this.lateCancelBillable,
      this.distanceBasis,
      this.basis,
      this.ratePerKm})
      : super._();
  @override
  BillingExportTreatment rebuild(
          void Function(BillingExportTreatmentBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  BillingExportTreatmentBuilder toBuilder() =>
      BillingExportTreatmentBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is BillingExportTreatment &&
        noShowBillable == other.noShowBillable &&
        lateCancelBillable == other.lateCancelBillable &&
        distanceBasis == other.distanceBasis &&
        basis == other.basis &&
        ratePerKm == other.ratePerKm;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, noShowBillable.hashCode);
    _$hash = $jc(_$hash, lateCancelBillable.hashCode);
    _$hash = $jc(_$hash, distanceBasis.hashCode);
    _$hash = $jc(_$hash, basis.hashCode);
    _$hash = $jc(_$hash, ratePerKm.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportTreatment')
          ..add('noShowBillable', noShowBillable)
          ..add('lateCancelBillable', lateCancelBillable)
          ..add('distanceBasis', distanceBasis)
          ..add('basis', basis)
          ..add('ratePerKm', ratePerKm))
        .toString();
  }
}

class BillingExportTreatmentBuilder
    implements Builder<BillingExportTreatment, BillingExportTreatmentBuilder> {
  _$BillingExportTreatment? _$v;

  bool? _noShowBillable;
  bool? get noShowBillable => _$this._noShowBillable;
  set noShowBillable(bool? noShowBillable) =>
      _$this._noShowBillable = noShowBillable;

  bool? _lateCancelBillable;
  bool? get lateCancelBillable => _$this._lateCancelBillable;
  set lateCancelBillable(bool? lateCancelBillable) =>
      _$this._lateCancelBillable = lateCancelBillable;

  BillingExportTreatmentDistanceBasisEnum? _distanceBasis;
  BillingExportTreatmentDistanceBasisEnum? get distanceBasis =>
      _$this._distanceBasis;
  set distanceBasis(BillingExportTreatmentDistanceBasisEnum? distanceBasis) =>
      _$this._distanceBasis = distanceBasis;

  BillingExportTreatmentBasisEnum? _basis;
  BillingExportTreatmentBasisEnum? get basis => _$this._basis;
  set basis(BillingExportTreatmentBasisEnum? basis) => _$this._basis = basis;

  num? _ratePerKm;
  num? get ratePerKm => _$this._ratePerKm;
  set ratePerKm(num? ratePerKm) => _$this._ratePerKm = ratePerKm;

  BillingExportTreatmentBuilder() {
    BillingExportTreatment._defaults(this);
  }

  BillingExportTreatmentBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _noShowBillable = $v.noShowBillable;
      _lateCancelBillable = $v.lateCancelBillable;
      _distanceBasis = $v.distanceBasis;
      _basis = $v.basis;
      _ratePerKm = $v.ratePerKm;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(BillingExportTreatment other) {
    _$v = other as _$BillingExportTreatment;
  }

  @override
  void update(void Function(BillingExportTreatmentBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  BillingExportTreatment build() => _build();

  _$BillingExportTreatment _build() {
    final _$result = _$v ??
        _$BillingExportTreatment._(
          noShowBillable: noShowBillable,
          lateCancelBillable: lateCancelBillable,
          distanceBasis: distanceBasis,
          basis: basis,
          ratePerKm: ratePerKm,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
