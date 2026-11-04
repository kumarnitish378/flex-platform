// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_treatment.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const BillingExportTreatmentBasisEnum
    _$billingExportTreatmentBasisEnum_perCabPerDayKm =
    const BillingExportTreatmentBasisEnum._('perCabPerDayKm');

BillingExportTreatmentBasisEnum _$billingExportTreatmentBasisEnumValueOf(
    String name) {
  switch (name) {
    case 'perCabPerDayKm':
      return _$billingExportTreatmentBasisEnum_perCabPerDayKm;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<BillingExportTreatmentBasisEnum>
    _$billingExportTreatmentBasisEnumValues = BuiltSet<
        BillingExportTreatmentBasisEnum>(const <BillingExportTreatmentBasisEnum>[
  _$billingExportTreatmentBasisEnum_perCabPerDayKm,
]);

Serializer<BillingExportTreatmentBasisEnum>
    _$billingExportTreatmentBasisEnumSerializer =
    _$BillingExportTreatmentBasisEnumSerializer();

class _$BillingExportTreatmentBasisEnumSerializer
    implements PrimitiveSerializer<BillingExportTreatmentBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'perCabPerDayKm': 'per_cab_per_day_km',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'per_cab_per_day_km': 'perCabPerDayKm',
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
  final BillingExportTreatmentBasisEnum? basis;
  @override
  final num? ratePerKm;
  @override
  final num? odometerGapThresholdPercent;
  @override
  final String? defaultClientId;

  factory _$BillingExportTreatment(
          [void Function(BillingExportTreatmentBuilder)? updates]) =>
      (BillingExportTreatmentBuilder()..update(updates))._build();

  _$BillingExportTreatment._(
      {this.basis,
      this.ratePerKm,
      this.odometerGapThresholdPercent,
      this.defaultClientId})
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
        basis == other.basis &&
        ratePerKm == other.ratePerKm &&
        odometerGapThresholdPercent == other.odometerGapThresholdPercent &&
        defaultClientId == other.defaultClientId;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, basis.hashCode);
    _$hash = $jc(_$hash, ratePerKm.hashCode);
    _$hash = $jc(_$hash, odometerGapThresholdPercent.hashCode);
    _$hash = $jc(_$hash, defaultClientId.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportTreatment')
          ..add('basis', basis)
          ..add('ratePerKm', ratePerKm)
          ..add('odometerGapThresholdPercent', odometerGapThresholdPercent)
          ..add('defaultClientId', defaultClientId))
        .toString();
  }
}

class BillingExportTreatmentBuilder
    implements Builder<BillingExportTreatment, BillingExportTreatmentBuilder> {
  _$BillingExportTreatment? _$v;

  BillingExportTreatmentBasisEnum? _basis;
  BillingExportTreatmentBasisEnum? get basis => _$this._basis;
  set basis(BillingExportTreatmentBasisEnum? basis) => _$this._basis = basis;

  num? _ratePerKm;
  num? get ratePerKm => _$this._ratePerKm;
  set ratePerKm(num? ratePerKm) => _$this._ratePerKm = ratePerKm;

  num? _odometerGapThresholdPercent;
  num? get odometerGapThresholdPercent => _$this._odometerGapThresholdPercent;
  set odometerGapThresholdPercent(num? odometerGapThresholdPercent) =>
      _$this._odometerGapThresholdPercent = odometerGapThresholdPercent;

  String? _defaultClientId;
  String? get defaultClientId => _$this._defaultClientId;
  set defaultClientId(String? defaultClientId) =>
      _$this._defaultClientId = defaultClientId;

  BillingExportTreatmentBuilder() {
    BillingExportTreatment._defaults(this);
  }

  BillingExportTreatmentBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _basis = $v.basis;
      _ratePerKm = $v.ratePerKm;
      _odometerGapThresholdPercent = $v.odometerGapThresholdPercent;
      _defaultClientId = $v.defaultClientId;
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
          basis: basis,
          ratePerKm: ratePerKm,
          odometerGapThresholdPercent: odometerGapThresholdPercent,
          defaultClientId: defaultClientId,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
