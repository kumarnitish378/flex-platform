// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'employee.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Employee extends Employee {
  @override
  final String? clientId;
  @override
  final String? zoneId;
  @override
  final String? id;
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

  factory _$Employee([void Function(EmployeeBuilder)? updates]) =>
      (EmployeeBuilder()..update(updates))._build();

  _$Employee._(
      {this.clientId,
      this.zoneId,
      this.id,
      required this.name,
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
  Employee rebuild(void Function(EmployeeBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  EmployeeBuilder toBuilder() => EmployeeBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Employee &&
        clientId == other.clientId &&
        zoneId == other.zoneId &&
        id == other.id &&
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
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, zoneId.hashCode);
    _$hash = $jc(_$hash, id.hashCode);
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
    return (newBuiltValueToStringHelper(r'Employee')
          ..add('clientId', clientId)
          ..add('zoneId', zoneId)
          ..add('id', id)
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

class EmployeeBuilder
    implements Builder<Employee, EmployeeBuilder>, EmployeeInputBuilder {
  _$Employee? _$v;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(covariant String? clientId) => _$this._clientId = clientId;

  String? _zoneId;
  String? get zoneId => _$this._zoneId;
  set zoneId(covariant String? zoneId) => _$this._zoneId = zoneId;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

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

  EmployeeBuilder() {
    Employee._defaults(this);
  }

  EmployeeBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _clientId = $v.clientId;
      _zoneId = $v.zoneId;
      _id = $v.id;
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
  void replace(covariant Employee other) {
    _$v = other as _$Employee;
  }

  @override
  void update(void Function(EmployeeBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Employee build() => _build();

  _$Employee _build() {
    _$Employee _$result;
    try {
      _$result = _$v ??
          _$Employee._(
            clientId: clientId,
            zoneId: zoneId,
            id: id,
            name: BuiltValueNullFieldError.checkNotNull(
                name, r'Employee', 'name'),
            phone: BuiltValueNullFieldError.checkNotNull(
                phone, r'Employee', 'phone'),
            officeId: BuiltValueNullFieldError.checkNotNull(
                officeId, r'Employee', 'officeId'),
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
            r'Employee', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
