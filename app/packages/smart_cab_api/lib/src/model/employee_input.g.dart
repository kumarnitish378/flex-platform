// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'employee_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class EmployeeInputBuilder {
  void replace(EmployeeInput other);
  void update(void Function(EmployeeInputBuilder) updates);
  String? get name;
  set name(String? name);

  String? get phone;
  set phone(String? phone);

  String? get officeId;
  set officeId(String? officeId);

  LatLngBuilder get homeLocation;
  set homeLocation(LatLngBuilder? homeLocation);

  String? get homeLandmark;
  set homeLandmark(String? homeLandmark);

  int? get priority;
  set priority(int? priority);

  bool? get isVip;
  set isVip(bool? isVip);

  bool? get nightEscortRequired;
  set nightEscortRequired(bool? nightEscortRequired);

  bool? get active;
  set active(bool? active);
}

class _$$EmployeeInput extends $EmployeeInput {
  @override
  final String name;
  @override
  final String phone;
  @override
  final String officeId;
  @override
  final LatLng homeLocation;
  @override
  final String? homeLandmark;
  @override
  final int? priority;
  @override
  final bool? isVip;
  @override
  final bool? nightEscortRequired;
  @override
  final bool? active;

  factory _$$EmployeeInput([void Function($EmployeeInputBuilder)? updates]) =>
      ($EmployeeInputBuilder()..update(updates))._build();

  _$$EmployeeInput._(
      {required this.name,
      required this.phone,
      required this.officeId,
      required this.homeLocation,
      this.homeLandmark,
      this.priority,
      this.isVip,
      this.nightEscortRequired,
      this.active})
      : super._();
  @override
  $EmployeeInput rebuild(void Function($EmployeeInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $EmployeeInputBuilder toBuilder() => $EmployeeInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $EmployeeInput &&
        name == other.name &&
        phone == other.phone &&
        officeId == other.officeId &&
        homeLocation == other.homeLocation &&
        homeLandmark == other.homeLandmark &&
        priority == other.priority &&
        isVip == other.isVip &&
        nightEscortRequired == other.nightEscortRequired &&
        active == other.active;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, phone.hashCode);
    _$hash = $jc(_$hash, officeId.hashCode);
    _$hash = $jc(_$hash, homeLocation.hashCode);
    _$hash = $jc(_$hash, homeLandmark.hashCode);
    _$hash = $jc(_$hash, priority.hashCode);
    _$hash = $jc(_$hash, isVip.hashCode);
    _$hash = $jc(_$hash, nightEscortRequired.hashCode);
    _$hash = $jc(_$hash, active.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'$EmployeeInput')
          ..add('name', name)
          ..add('phone', phone)
          ..add('officeId', officeId)
          ..add('homeLocation', homeLocation)
          ..add('homeLandmark', homeLandmark)
          ..add('priority', priority)
          ..add('isVip', isVip)
          ..add('nightEscortRequired', nightEscortRequired)
          ..add('active', active))
        .toString();
  }
}

class $EmployeeInputBuilder
    implements
        Builder<$EmployeeInput, $EmployeeInputBuilder>,
        EmployeeInputBuilder {
  _$$EmployeeInput? _$v;

  String? _name;
  String? get name => _$this._name;
  set name(covariant String? name) => _$this._name = name;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(covariant String? phone) => _$this._phone = phone;

  String? _officeId;
  String? get officeId => _$this._officeId;
  set officeId(covariant String? officeId) => _$this._officeId = officeId;

  LatLngBuilder? _homeLocation;
  LatLngBuilder get homeLocation => _$this._homeLocation ??= LatLngBuilder();
  set homeLocation(covariant LatLngBuilder? homeLocation) =>
      _$this._homeLocation = homeLocation;

  String? _homeLandmark;
  String? get homeLandmark => _$this._homeLandmark;
  set homeLandmark(covariant String? homeLandmark) =>
      _$this._homeLandmark = homeLandmark;

  int? _priority;
  int? get priority => _$this._priority;
  set priority(covariant int? priority) => _$this._priority = priority;

  bool? _isVip;
  bool? get isVip => _$this._isVip;
  set isVip(covariant bool? isVip) => _$this._isVip = isVip;

  bool? _nightEscortRequired;
  bool? get nightEscortRequired => _$this._nightEscortRequired;
  set nightEscortRequired(covariant bool? nightEscortRequired) =>
      _$this._nightEscortRequired = nightEscortRequired;

  bool? _active;
  bool? get active => _$this._active;
  set active(covariant bool? active) => _$this._active = active;

  $EmployeeInputBuilder() {
    $EmployeeInput._defaults(this);
  }

  $EmployeeInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _name = $v.name;
      _phone = $v.phone;
      _officeId = $v.officeId;
      _homeLocation = $v.homeLocation.toBuilder();
      _homeLandmark = $v.homeLandmark;
      _priority = $v.priority;
      _isVip = $v.isVip;
      _nightEscortRequired = $v.nightEscortRequired;
      _active = $v.active;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant $EmployeeInput other) {
    _$v = other as _$$EmployeeInput;
  }

  @override
  void update(void Function($EmployeeInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $EmployeeInput build() => _build();

  _$$EmployeeInput _build() {
    _$$EmployeeInput _$result;
    try {
      _$result = _$v ??
          _$$EmployeeInput._(
            name: BuiltValueNullFieldError.checkNotNull(
                name, r'$EmployeeInput', 'name'),
            phone: BuiltValueNullFieldError.checkNotNull(
                phone, r'$EmployeeInput', 'phone'),
            officeId: BuiltValueNullFieldError.checkNotNull(
                officeId, r'$EmployeeInput', 'officeId'),
            homeLocation: homeLocation.build(),
            homeLandmark: homeLandmark,
            priority: priority,
            isVip: isVip,
            nightEscortRequired: nightEscortRequired,
            active: active,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'homeLocation';
        homeLocation.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'$EmployeeInput', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
