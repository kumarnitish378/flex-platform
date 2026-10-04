// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'candidate.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Candidate extends Candidate {
  @override
  final String? vehicleId;
  @override
  final String? registrationNo;
  @override
  final String? tripId;
  @override
  final int? etaToPickupSeconds;
  @override
  final bool? etaApproximate;
  @override
  final int? seatsFreeAfter;
  @override
  final num? gpsAgeSeconds;
  @override
  final BuiltList<CandidateAddedMinutesExistingInner>? addedMinutesExisting;
  @override
  final num? emptyKmAdded;
  @override
  final bool? newTrip;
  @override
  final num? cost;
  @override
  final BuiltList<String>? reasons;
  @override
  final BuiltList<String>? violations;

  factory _$Candidate([void Function(CandidateBuilder)? updates]) =>
      (CandidateBuilder()..update(updates))._build();

  _$Candidate._(
      {this.vehicleId,
      this.registrationNo,
      this.tripId,
      this.etaToPickupSeconds,
      this.etaApproximate,
      this.seatsFreeAfter,
      this.gpsAgeSeconds,
      this.addedMinutesExisting,
      this.emptyKmAdded,
      this.newTrip,
      this.cost,
      this.reasons,
      this.violations})
      : super._();
  @override
  Candidate rebuild(void Function(CandidateBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  CandidateBuilder toBuilder() => CandidateBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Candidate &&
        vehicleId == other.vehicleId &&
        registrationNo == other.registrationNo &&
        tripId == other.tripId &&
        etaToPickupSeconds == other.etaToPickupSeconds &&
        etaApproximate == other.etaApproximate &&
        seatsFreeAfter == other.seatsFreeAfter &&
        gpsAgeSeconds == other.gpsAgeSeconds &&
        addedMinutesExisting == other.addedMinutesExisting &&
        emptyKmAdded == other.emptyKmAdded &&
        newTrip == other.newTrip &&
        cost == other.cost &&
        reasons == other.reasons &&
        violations == other.violations;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, registrationNo.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, etaToPickupSeconds.hashCode);
    _$hash = $jc(_$hash, etaApproximate.hashCode);
    _$hash = $jc(_$hash, seatsFreeAfter.hashCode);
    _$hash = $jc(_$hash, gpsAgeSeconds.hashCode);
    _$hash = $jc(_$hash, addedMinutesExisting.hashCode);
    _$hash = $jc(_$hash, emptyKmAdded.hashCode);
    _$hash = $jc(_$hash, newTrip.hashCode);
    _$hash = $jc(_$hash, cost.hashCode);
    _$hash = $jc(_$hash, reasons.hashCode);
    _$hash = $jc(_$hash, violations.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Candidate')
          ..add('vehicleId', vehicleId)
          ..add('registrationNo', registrationNo)
          ..add('tripId', tripId)
          ..add('etaToPickupSeconds', etaToPickupSeconds)
          ..add('etaApproximate', etaApproximate)
          ..add('seatsFreeAfter', seatsFreeAfter)
          ..add('gpsAgeSeconds', gpsAgeSeconds)
          ..add('addedMinutesExisting', addedMinutesExisting)
          ..add('emptyKmAdded', emptyKmAdded)
          ..add('newTrip', newTrip)
          ..add('cost', cost)
          ..add('reasons', reasons)
          ..add('violations', violations))
        .toString();
  }
}

class CandidateBuilder implements Builder<Candidate, CandidateBuilder> {
  _$Candidate? _$v;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  String? _registrationNo;
  String? get registrationNo => _$this._registrationNo;
  set registrationNo(String? registrationNo) =>
      _$this._registrationNo = registrationNo;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  int? _etaToPickupSeconds;
  int? get etaToPickupSeconds => _$this._etaToPickupSeconds;
  set etaToPickupSeconds(int? etaToPickupSeconds) =>
      _$this._etaToPickupSeconds = etaToPickupSeconds;

  bool? _etaApproximate;
  bool? get etaApproximate => _$this._etaApproximate;
  set etaApproximate(bool? etaApproximate) =>
      _$this._etaApproximate = etaApproximate;

  int? _seatsFreeAfter;
  int? get seatsFreeAfter => _$this._seatsFreeAfter;
  set seatsFreeAfter(int? seatsFreeAfter) =>
      _$this._seatsFreeAfter = seatsFreeAfter;

  num? _gpsAgeSeconds;
  num? get gpsAgeSeconds => _$this._gpsAgeSeconds;
  set gpsAgeSeconds(num? gpsAgeSeconds) =>
      _$this._gpsAgeSeconds = gpsAgeSeconds;

  ListBuilder<CandidateAddedMinutesExistingInner>? _addedMinutesExisting;
  ListBuilder<CandidateAddedMinutesExistingInner> get addedMinutesExisting =>
      _$this._addedMinutesExisting ??=
          ListBuilder<CandidateAddedMinutesExistingInner>();
  set addedMinutesExisting(
          ListBuilder<CandidateAddedMinutesExistingInner>?
              addedMinutesExisting) =>
      _$this._addedMinutesExisting = addedMinutesExisting;

  num? _emptyKmAdded;
  num? get emptyKmAdded => _$this._emptyKmAdded;
  set emptyKmAdded(num? emptyKmAdded) => _$this._emptyKmAdded = emptyKmAdded;

  bool? _newTrip;
  bool? get newTrip => _$this._newTrip;
  set newTrip(bool? newTrip) => _$this._newTrip = newTrip;

  num? _cost;
  num? get cost => _$this._cost;
  set cost(num? cost) => _$this._cost = cost;

  ListBuilder<String>? _reasons;
  ListBuilder<String> get reasons => _$this._reasons ??= ListBuilder<String>();
  set reasons(ListBuilder<String>? reasons) => _$this._reasons = reasons;

  ListBuilder<String>? _violations;
  ListBuilder<String> get violations =>
      _$this._violations ??= ListBuilder<String>();
  set violations(ListBuilder<String>? violations) =>
      _$this._violations = violations;

  CandidateBuilder() {
    Candidate._defaults(this);
  }

  CandidateBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _vehicleId = $v.vehicleId;
      _registrationNo = $v.registrationNo;
      _tripId = $v.tripId;
      _etaToPickupSeconds = $v.etaToPickupSeconds;
      _etaApproximate = $v.etaApproximate;
      _seatsFreeAfter = $v.seatsFreeAfter;
      _gpsAgeSeconds = $v.gpsAgeSeconds;
      _addedMinutesExisting = $v.addedMinutesExisting?.toBuilder();
      _emptyKmAdded = $v.emptyKmAdded;
      _newTrip = $v.newTrip;
      _cost = $v.cost;
      _reasons = $v.reasons?.toBuilder();
      _violations = $v.violations?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(Candidate other) {
    _$v = other as _$Candidate;
  }

  @override
  void update(void Function(CandidateBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Candidate build() => _build();

  _$Candidate _build() {
    _$Candidate _$result;
    try {
      _$result = _$v ??
          _$Candidate._(
            vehicleId: vehicleId,
            registrationNo: registrationNo,
            tripId: tripId,
            etaToPickupSeconds: etaToPickupSeconds,
            etaApproximate: etaApproximate,
            seatsFreeAfter: seatsFreeAfter,
            gpsAgeSeconds: gpsAgeSeconds,
            addedMinutesExisting: _addedMinutesExisting?.build(),
            emptyKmAdded: emptyKmAdded,
            newTrip: newTrip,
            cost: cost,
            reasons: _reasons?.build(),
            violations: _violations?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'addedMinutesExisting';
        _addedMinutesExisting?.build();

        _$failedField = 'reasons';
        _reasons?.build();
        _$failedField = 'violations';
        _violations?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'Candidate', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
