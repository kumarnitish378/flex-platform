// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_rows_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const BillingExportRowsInnerFlagsEnum
    _$billingExportRowsInnerFlagsEnum_odometerGap =
    const BillingExportRowsInnerFlagsEnum._('odometerGap');
const BillingExportRowsInnerFlagsEnum
    _$billingExportRowsInnerFlagsEnum_multipleClients =
    const BillingExportRowsInnerFlagsEnum._('multipleClients');
const BillingExportRowsInnerFlagsEnum
    _$billingExportRowsInnerFlagsEnum_noClientTrips =
    const BillingExportRowsInnerFlagsEnum._('noClientTrips');
const BillingExportRowsInnerFlagsEnum
    _$billingExportRowsInnerFlagsEnum_defaultClientUnset =
    const BillingExportRowsInnerFlagsEnum._('defaultClientUnset');
const BillingExportRowsInnerFlagsEnum
    _$billingExportRowsInnerFlagsEnum_stillOnDuty =
    const BillingExportRowsInnerFlagsEnum._('stillOnDuty');
const BillingExportRowsInnerFlagsEnum _$billingExportRowsInnerFlagsEnum_noGps =
    const BillingExportRowsInnerFlagsEnum._('noGps');
const BillingExportRowsInnerFlagsEnum
    _$billingExportRowsInnerFlagsEnum_odometerBilled =
    const BillingExportRowsInnerFlagsEnum._('odometerBilled');

BillingExportRowsInnerFlagsEnum _$billingExportRowsInnerFlagsEnumValueOf(
    String name) {
  switch (name) {
    case 'odometerGap':
      return _$billingExportRowsInnerFlagsEnum_odometerGap;
    case 'multipleClients':
      return _$billingExportRowsInnerFlagsEnum_multipleClients;
    case 'noClientTrips':
      return _$billingExportRowsInnerFlagsEnum_noClientTrips;
    case 'defaultClientUnset':
      return _$billingExportRowsInnerFlagsEnum_defaultClientUnset;
    case 'stillOnDuty':
      return _$billingExportRowsInnerFlagsEnum_stillOnDuty;
    case 'noGps':
      return _$billingExportRowsInnerFlagsEnum_noGps;
    case 'odometerBilled':
      return _$billingExportRowsInnerFlagsEnum_odometerBilled;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<BillingExportRowsInnerFlagsEnum>
    _$billingExportRowsInnerFlagsEnumValues = BuiltSet<
        BillingExportRowsInnerFlagsEnum>(const <BillingExportRowsInnerFlagsEnum>[
  _$billingExportRowsInnerFlagsEnum_odometerGap,
  _$billingExportRowsInnerFlagsEnum_multipleClients,
  _$billingExportRowsInnerFlagsEnum_noClientTrips,
  _$billingExportRowsInnerFlagsEnum_defaultClientUnset,
  _$billingExportRowsInnerFlagsEnum_stillOnDuty,
  _$billingExportRowsInnerFlagsEnum_noGps,
  _$billingExportRowsInnerFlagsEnum_odometerBilled,
]);

Serializer<BillingExportRowsInnerFlagsEnum>
    _$billingExportRowsInnerFlagsEnumSerializer =
    _$BillingExportRowsInnerFlagsEnumSerializer();

class _$BillingExportRowsInnerFlagsEnumSerializer
    implements PrimitiveSerializer<BillingExportRowsInnerFlagsEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'odometerGap': 'odometer_gap',
    'multipleClients': 'multiple_clients',
    'noClientTrips': 'no_client_trips',
    'defaultClientUnset': 'default_client_unset',
    'stillOnDuty': 'still_on_duty',
    'noGps': 'no_gps',
    'odometerBilled': 'odometer_billed',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'odometer_gap': 'odometerGap',
    'multiple_clients': 'multipleClients',
    'no_client_trips': 'noClientTrips',
    'default_client_unset': 'defaultClientUnset',
    'still_on_duty': 'stillOnDuty',
    'no_gps': 'noGps',
    'odometer_billed': 'odometerBilled',
  };

  @override
  final Iterable<Type> types = const <Type>[BillingExportRowsInnerFlagsEnum];
  @override
  final String wireName = 'BillingExportRowsInnerFlagsEnum';

  @override
  Object serialize(
          Serializers serializers, BillingExportRowsInnerFlagsEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  BillingExportRowsInnerFlagsEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      BillingExportRowsInnerFlagsEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$BillingExportRowsInner extends BillingExportRowsInner {
  @override
  final Date? date;
  @override
  final String? cab;
  @override
  final BuiltList<String>? drivers;
  @override
  final DateTime? dutyIn;
  @override
  final DateTime? dutyOut;
  @override
  final num? gpsKm;
  @override
  final num? odometerKm;
  @override
  final num? gapPercent;
  @override
  final num? billedKm;
  @override
  final num? ratePerKm;
  @override
  final num? amount;
  @override
  final BuiltList<BillingExportRowsInnerFlagsEnum>? flags;
  @override
  final BuiltList<BillingExportRowsInnerSessionsInner>? sessions;

  factory _$BillingExportRowsInner(
          [void Function(BillingExportRowsInnerBuilder)? updates]) =>
      (BillingExportRowsInnerBuilder()..update(updates))._build();

  _$BillingExportRowsInner._(
      {this.date,
      this.cab,
      this.drivers,
      this.dutyIn,
      this.dutyOut,
      this.gpsKm,
      this.odometerKm,
      this.gapPercent,
      this.billedKm,
      this.ratePerKm,
      this.amount,
      this.flags,
      this.sessions})
      : super._();
  @override
  BillingExportRowsInner rebuild(
          void Function(BillingExportRowsInnerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  BillingExportRowsInnerBuilder toBuilder() =>
      BillingExportRowsInnerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is BillingExportRowsInner &&
        date == other.date &&
        cab == other.cab &&
        drivers == other.drivers &&
        dutyIn == other.dutyIn &&
        dutyOut == other.dutyOut &&
        gpsKm == other.gpsKm &&
        odometerKm == other.odometerKm &&
        gapPercent == other.gapPercent &&
        billedKm == other.billedKm &&
        ratePerKm == other.ratePerKm &&
        amount == other.amount &&
        flags == other.flags &&
        sessions == other.sessions;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, date.hashCode);
    _$hash = $jc(_$hash, cab.hashCode);
    _$hash = $jc(_$hash, drivers.hashCode);
    _$hash = $jc(_$hash, dutyIn.hashCode);
    _$hash = $jc(_$hash, dutyOut.hashCode);
    _$hash = $jc(_$hash, gpsKm.hashCode);
    _$hash = $jc(_$hash, odometerKm.hashCode);
    _$hash = $jc(_$hash, gapPercent.hashCode);
    _$hash = $jc(_$hash, billedKm.hashCode);
    _$hash = $jc(_$hash, ratePerKm.hashCode);
    _$hash = $jc(_$hash, amount.hashCode);
    _$hash = $jc(_$hash, flags.hashCode);
    _$hash = $jc(_$hash, sessions.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportRowsInner')
          ..add('date', date)
          ..add('cab', cab)
          ..add('drivers', drivers)
          ..add('dutyIn', dutyIn)
          ..add('dutyOut', dutyOut)
          ..add('gpsKm', gpsKm)
          ..add('odometerKm', odometerKm)
          ..add('gapPercent', gapPercent)
          ..add('billedKm', billedKm)
          ..add('ratePerKm', ratePerKm)
          ..add('amount', amount)
          ..add('flags', flags)
          ..add('sessions', sessions))
        .toString();
  }
}

class BillingExportRowsInnerBuilder
    implements Builder<BillingExportRowsInner, BillingExportRowsInnerBuilder> {
  _$BillingExportRowsInner? _$v;

  Date? _date;
  Date? get date => _$this._date;
  set date(Date? date) => _$this._date = date;

  String? _cab;
  String? get cab => _$this._cab;
  set cab(String? cab) => _$this._cab = cab;

  ListBuilder<String>? _drivers;
  ListBuilder<String> get drivers => _$this._drivers ??= ListBuilder<String>();
  set drivers(ListBuilder<String>? drivers) => _$this._drivers = drivers;

  DateTime? _dutyIn;
  DateTime? get dutyIn => _$this._dutyIn;
  set dutyIn(DateTime? dutyIn) => _$this._dutyIn = dutyIn;

  DateTime? _dutyOut;
  DateTime? get dutyOut => _$this._dutyOut;
  set dutyOut(DateTime? dutyOut) => _$this._dutyOut = dutyOut;

  num? _gpsKm;
  num? get gpsKm => _$this._gpsKm;
  set gpsKm(num? gpsKm) => _$this._gpsKm = gpsKm;

  num? _odometerKm;
  num? get odometerKm => _$this._odometerKm;
  set odometerKm(num? odometerKm) => _$this._odometerKm = odometerKm;

  num? _gapPercent;
  num? get gapPercent => _$this._gapPercent;
  set gapPercent(num? gapPercent) => _$this._gapPercent = gapPercent;

  num? _billedKm;
  num? get billedKm => _$this._billedKm;
  set billedKm(num? billedKm) => _$this._billedKm = billedKm;

  num? _ratePerKm;
  num? get ratePerKm => _$this._ratePerKm;
  set ratePerKm(num? ratePerKm) => _$this._ratePerKm = ratePerKm;

  num? _amount;
  num? get amount => _$this._amount;
  set amount(num? amount) => _$this._amount = amount;

  ListBuilder<BillingExportRowsInnerFlagsEnum>? _flags;
  ListBuilder<BillingExportRowsInnerFlagsEnum> get flags =>
      _$this._flags ??= ListBuilder<BillingExportRowsInnerFlagsEnum>();
  set flags(ListBuilder<BillingExportRowsInnerFlagsEnum>? flags) =>
      _$this._flags = flags;

  ListBuilder<BillingExportRowsInnerSessionsInner>? _sessions;
  ListBuilder<BillingExportRowsInnerSessionsInner> get sessions =>
      _$this._sessions ??= ListBuilder<BillingExportRowsInnerSessionsInner>();
  set sessions(ListBuilder<BillingExportRowsInnerSessionsInner>? sessions) =>
      _$this._sessions = sessions;

  BillingExportRowsInnerBuilder() {
    BillingExportRowsInner._defaults(this);
  }

  BillingExportRowsInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _date = $v.date;
      _cab = $v.cab;
      _drivers = $v.drivers?.toBuilder();
      _dutyIn = $v.dutyIn;
      _dutyOut = $v.dutyOut;
      _gpsKm = $v.gpsKm;
      _odometerKm = $v.odometerKm;
      _gapPercent = $v.gapPercent;
      _billedKm = $v.billedKm;
      _ratePerKm = $v.ratePerKm;
      _amount = $v.amount;
      _flags = $v.flags?.toBuilder();
      _sessions = $v.sessions?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(BillingExportRowsInner other) {
    _$v = other as _$BillingExportRowsInner;
  }

  @override
  void update(void Function(BillingExportRowsInnerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  BillingExportRowsInner build() => _build();

  _$BillingExportRowsInner _build() {
    _$BillingExportRowsInner _$result;
    try {
      _$result = _$v ??
          _$BillingExportRowsInner._(
            date: date,
            cab: cab,
            drivers: _drivers?.build(),
            dutyIn: dutyIn,
            dutyOut: dutyOut,
            gpsKm: gpsKm,
            odometerKm: odometerKm,
            gapPercent: gapPercent,
            billedKm: billedKm,
            ratePerKm: ratePerKm,
            amount: amount,
            flags: _flags?.build(),
            sessions: _sessions?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'drivers';
        _drivers?.build();

        _$failedField = 'flags';
        _flags?.build();
        _$failedField = 'sessions';
        _sessions?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'BillingExportRowsInner', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
