// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_rows_inner_sessions_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const BillingExportRowsInnerSessionsInnerBasisEnum
    _$billingExportRowsInnerSessionsInnerBasisEnum_gps =
    const BillingExportRowsInnerSessionsInnerBasisEnum._('gps');
const BillingExportRowsInnerSessionsInnerBasisEnum
    _$billingExportRowsInnerSessionsInnerBasisEnum_odometer =
    const BillingExportRowsInnerSessionsInnerBasisEnum._('odometer');

BillingExportRowsInnerSessionsInnerBasisEnum
    _$billingExportRowsInnerSessionsInnerBasisEnumValueOf(String name) {
  switch (name) {
    case 'gps':
      return _$billingExportRowsInnerSessionsInnerBasisEnum_gps;
    case 'odometer':
      return _$billingExportRowsInnerSessionsInnerBasisEnum_odometer;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<BillingExportRowsInnerSessionsInnerBasisEnum>
    _$billingExportRowsInnerSessionsInnerBasisEnumValues = BuiltSet<
        BillingExportRowsInnerSessionsInnerBasisEnum>(const <BillingExportRowsInnerSessionsInnerBasisEnum>[
  _$billingExportRowsInnerSessionsInnerBasisEnum_gps,
  _$billingExportRowsInnerSessionsInnerBasisEnum_odometer,
]);

Serializer<BillingExportRowsInnerSessionsInnerBasisEnum>
    _$billingExportRowsInnerSessionsInnerBasisEnumSerializer =
    _$BillingExportRowsInnerSessionsInnerBasisEnumSerializer();

class _$BillingExportRowsInnerSessionsInnerBasisEnumSerializer
    implements
        PrimitiveSerializer<BillingExportRowsInnerSessionsInnerBasisEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'gps': 'gps',
    'odometer': 'odometer',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'gps': 'gps',
    'odometer': 'odometer',
  };

  @override
  final Iterable<Type> types = const <Type>[
    BillingExportRowsInnerSessionsInnerBasisEnum
  ];
  @override
  final String wireName = 'BillingExportRowsInnerSessionsInnerBasisEnum';

  @override
  Object serialize(Serializers serializers,
          BillingExportRowsInnerSessionsInnerBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  BillingExportRowsInnerSessionsInnerBasisEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      BillingExportRowsInnerSessionsInnerBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$BillingExportRowsInnerSessionsInner
    extends BillingExportRowsInnerSessionsInner {
  @override
  final String? id;
  @override
  final String? driver;
  @override
  final DateTime? dutyIn;
  @override
  final DateTime? dutyOut;
  @override
  final num? gpsKm;
  @override
  final num? odometerStartKm;
  @override
  final num? odometerEndKm;
  @override
  final num? odometerKm;
  @override
  final BillingExportRowsInnerSessionsInnerBasisEnum? basis;

  factory _$BillingExportRowsInnerSessionsInner(
          [void Function(BillingExportRowsInnerSessionsInnerBuilder)?
              updates]) =>
      (BillingExportRowsInnerSessionsInnerBuilder()..update(updates))._build();

  _$BillingExportRowsInnerSessionsInner._(
      {this.id,
      this.driver,
      this.dutyIn,
      this.dutyOut,
      this.gpsKm,
      this.odometerStartKm,
      this.odometerEndKm,
      this.odometerKm,
      this.basis})
      : super._();
  @override
  BillingExportRowsInnerSessionsInner rebuild(
          void Function(BillingExportRowsInnerSessionsInnerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  BillingExportRowsInnerSessionsInnerBuilder toBuilder() =>
      BillingExportRowsInnerSessionsInnerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is BillingExportRowsInnerSessionsInner &&
        id == other.id &&
        driver == other.driver &&
        dutyIn == other.dutyIn &&
        dutyOut == other.dutyOut &&
        gpsKm == other.gpsKm &&
        odometerStartKm == other.odometerStartKm &&
        odometerEndKm == other.odometerEndKm &&
        odometerKm == other.odometerKm &&
        basis == other.basis;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, driver.hashCode);
    _$hash = $jc(_$hash, dutyIn.hashCode);
    _$hash = $jc(_$hash, dutyOut.hashCode);
    _$hash = $jc(_$hash, gpsKm.hashCode);
    _$hash = $jc(_$hash, odometerStartKm.hashCode);
    _$hash = $jc(_$hash, odometerEndKm.hashCode);
    _$hash = $jc(_$hash, odometerKm.hashCode);
    _$hash = $jc(_$hash, basis.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportRowsInnerSessionsInner')
          ..add('id', id)
          ..add('driver', driver)
          ..add('dutyIn', dutyIn)
          ..add('dutyOut', dutyOut)
          ..add('gpsKm', gpsKm)
          ..add('odometerStartKm', odometerStartKm)
          ..add('odometerEndKm', odometerEndKm)
          ..add('odometerKm', odometerKm)
          ..add('basis', basis))
        .toString();
  }
}

class BillingExportRowsInnerSessionsInnerBuilder
    implements
        Builder<BillingExportRowsInnerSessionsInner,
            BillingExportRowsInnerSessionsInnerBuilder> {
  _$BillingExportRowsInnerSessionsInner? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  String? _driver;
  String? get driver => _$this._driver;
  set driver(String? driver) => _$this._driver = driver;

  DateTime? _dutyIn;
  DateTime? get dutyIn => _$this._dutyIn;
  set dutyIn(DateTime? dutyIn) => _$this._dutyIn = dutyIn;

  DateTime? _dutyOut;
  DateTime? get dutyOut => _$this._dutyOut;
  set dutyOut(DateTime? dutyOut) => _$this._dutyOut = dutyOut;

  num? _gpsKm;
  num? get gpsKm => _$this._gpsKm;
  set gpsKm(num? gpsKm) => _$this._gpsKm = gpsKm;

  num? _odometerStartKm;
  num? get odometerStartKm => _$this._odometerStartKm;
  set odometerStartKm(num? odometerStartKm) =>
      _$this._odometerStartKm = odometerStartKm;

  num? _odometerEndKm;
  num? get odometerEndKm => _$this._odometerEndKm;
  set odometerEndKm(num? odometerEndKm) =>
      _$this._odometerEndKm = odometerEndKm;

  num? _odometerKm;
  num? get odometerKm => _$this._odometerKm;
  set odometerKm(num? odometerKm) => _$this._odometerKm = odometerKm;

  BillingExportRowsInnerSessionsInnerBasisEnum? _basis;
  BillingExportRowsInnerSessionsInnerBasisEnum? get basis => _$this._basis;
  set basis(BillingExportRowsInnerSessionsInnerBasisEnum? basis) =>
      _$this._basis = basis;

  BillingExportRowsInnerSessionsInnerBuilder() {
    BillingExportRowsInnerSessionsInner._defaults(this);
  }

  BillingExportRowsInnerSessionsInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _driver = $v.driver;
      _dutyIn = $v.dutyIn;
      _dutyOut = $v.dutyOut;
      _gpsKm = $v.gpsKm;
      _odometerStartKm = $v.odometerStartKm;
      _odometerEndKm = $v.odometerEndKm;
      _odometerKm = $v.odometerKm;
      _basis = $v.basis;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(BillingExportRowsInnerSessionsInner other) {
    _$v = other as _$BillingExportRowsInnerSessionsInner;
  }

  @override
  void update(
      void Function(BillingExportRowsInnerSessionsInnerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  BillingExportRowsInnerSessionsInner build() => _build();

  _$BillingExportRowsInnerSessionsInner _build() {
    final _$result = _$v ??
        _$BillingExportRowsInnerSessionsInner._(
          id: id,
          driver: driver,
          dutyIn: dutyIn,
          dutyOut: dutyOut,
          gpsKm: gpsKm,
          odometerStartKm: odometerStartKm,
          odometerEndKm: odometerEndKm,
          odometerKm: odometerKm,
          basis: basis,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
