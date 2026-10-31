// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_rows_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$BillingExportRowsInner extends BillingExportRowsInner {
  @override
  final Date? date;
  @override
  final String? requestId;
  @override
  final String? employee;
  @override
  final String? direction;
  @override
  final String? status;
  @override
  final bool? billable;
  @override
  final String? billableReason;
  @override
  final String? tripId;
  @override
  final String? vehicle;
  @override
  final int? ridersOnTrip;
  @override
  final num? directKm;
  @override
  final num? tripShareKm;
  @override
  final num? billableKm;

  factory _$BillingExportRowsInner(
          [void Function(BillingExportRowsInnerBuilder)? updates]) =>
      (BillingExportRowsInnerBuilder()..update(updates))._build();

  _$BillingExportRowsInner._(
      {this.date,
      this.requestId,
      this.employee,
      this.direction,
      this.status,
      this.billable,
      this.billableReason,
      this.tripId,
      this.vehicle,
      this.ridersOnTrip,
      this.directKm,
      this.tripShareKm,
      this.billableKm})
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
        requestId == other.requestId &&
        employee == other.employee &&
        direction == other.direction &&
        status == other.status &&
        billable == other.billable &&
        billableReason == other.billableReason &&
        tripId == other.tripId &&
        vehicle == other.vehicle &&
        ridersOnTrip == other.ridersOnTrip &&
        directKm == other.directKm &&
        tripShareKm == other.tripShareKm &&
        billableKm == other.billableKm;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, date.hashCode);
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, employee.hashCode);
    _$hash = $jc(_$hash, direction.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, billable.hashCode);
    _$hash = $jc(_$hash, billableReason.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, vehicle.hashCode);
    _$hash = $jc(_$hash, ridersOnTrip.hashCode);
    _$hash = $jc(_$hash, directKm.hashCode);
    _$hash = $jc(_$hash, tripShareKm.hashCode);
    _$hash = $jc(_$hash, billableKm.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportRowsInner')
          ..add('date', date)
          ..add('requestId', requestId)
          ..add('employee', employee)
          ..add('direction', direction)
          ..add('status', status)
          ..add('billable', billable)
          ..add('billableReason', billableReason)
          ..add('tripId', tripId)
          ..add('vehicle', vehicle)
          ..add('ridersOnTrip', ridersOnTrip)
          ..add('directKm', directKm)
          ..add('tripShareKm', tripShareKm)
          ..add('billableKm', billableKm))
        .toString();
  }
}

class BillingExportRowsInnerBuilder
    implements Builder<BillingExportRowsInner, BillingExportRowsInnerBuilder> {
  _$BillingExportRowsInner? _$v;

  Date? _date;
  Date? get date => _$this._date;
  set date(Date? date) => _$this._date = date;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _employee;
  String? get employee => _$this._employee;
  set employee(String? employee) => _$this._employee = employee;

  String? _direction;
  String? get direction => _$this._direction;
  set direction(String? direction) => _$this._direction = direction;

  String? _status;
  String? get status => _$this._status;
  set status(String? status) => _$this._status = status;

  bool? _billable;
  bool? get billable => _$this._billable;
  set billable(bool? billable) => _$this._billable = billable;

  String? _billableReason;
  String? get billableReason => _$this._billableReason;
  set billableReason(String? billableReason) =>
      _$this._billableReason = billableReason;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  String? _vehicle;
  String? get vehicle => _$this._vehicle;
  set vehicle(String? vehicle) => _$this._vehicle = vehicle;

  int? _ridersOnTrip;
  int? get ridersOnTrip => _$this._ridersOnTrip;
  set ridersOnTrip(int? ridersOnTrip) => _$this._ridersOnTrip = ridersOnTrip;

  num? _directKm;
  num? get directKm => _$this._directKm;
  set directKm(num? directKm) => _$this._directKm = directKm;

  num? _tripShareKm;
  num? get tripShareKm => _$this._tripShareKm;
  set tripShareKm(num? tripShareKm) => _$this._tripShareKm = tripShareKm;

  num? _billableKm;
  num? get billableKm => _$this._billableKm;
  set billableKm(num? billableKm) => _$this._billableKm = billableKm;

  BillingExportRowsInnerBuilder() {
    BillingExportRowsInner._defaults(this);
  }

  BillingExportRowsInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _date = $v.date;
      _requestId = $v.requestId;
      _employee = $v.employee;
      _direction = $v.direction;
      _status = $v.status;
      _billable = $v.billable;
      _billableReason = $v.billableReason;
      _tripId = $v.tripId;
      _vehicle = $v.vehicle;
      _ridersOnTrip = $v.ridersOnTrip;
      _directKm = $v.directKm;
      _tripShareKm = $v.tripShareKm;
      _billableKm = $v.billableKm;
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
    final _$result = _$v ??
        _$BillingExportRowsInner._(
          date: date,
          requestId: requestId,
          employee: employee,
          direction: direction,
          status: status,
          billable: billable,
          billableReason: billableReason,
          tripId: tripId,
          vehicle: vehicle,
          ridersOnTrip: ridersOnTrip,
          directKm: directKm,
          tripShareKm: tripShareKm,
          billableKm: billableKm,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
