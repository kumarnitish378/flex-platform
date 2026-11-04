// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_duty_sessions_session_id_billing_basis_put_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum
    _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_gps =
    const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum._('gps');
const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum
    _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_odometer =
    const AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum._(
        'odometer');

AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum
    _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnumValueOf(
        String name) {
  switch (name) {
    case 'gps':
      return _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_gps;
    case 'odometer':
      return _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_odometer;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum>
    _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnumValues =
    BuiltSet<
        AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum>(const <AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum>[
  _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_gps,
  _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnum_odometer,
]);

Serializer<AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum>
    _$adminDutySessionsSessionIdBillingBasisPutRequestBasisEnumSerializer =
    _$AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnumSerializer();

class _$AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnumSerializer
    implements
        PrimitiveSerializer<
            AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum> {
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
    AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum
  ];
  @override
  final String wireName =
      'AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum';

  @override
  Object serialize(Serializers serializers,
          AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$AdminDutySessionsSessionIdBillingBasisPutRequest
    extends AdminDutySessionsSessionIdBillingBasisPutRequest {
  @override
  final AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum basis;
  @override
  final String? note;

  factory _$AdminDutySessionsSessionIdBillingBasisPutRequest(
          [void Function(
                  AdminDutySessionsSessionIdBillingBasisPutRequestBuilder)?
              updates]) =>
      (AdminDutySessionsSessionIdBillingBasisPutRequestBuilder()
            ..update(updates))
          ._build();

  _$AdminDutySessionsSessionIdBillingBasisPutRequest._(
      {required this.basis, this.note})
      : super._();
  @override
  AdminDutySessionsSessionIdBillingBasisPutRequest rebuild(
          void Function(AdminDutySessionsSessionIdBillingBasisPutRequestBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminDutySessionsSessionIdBillingBasisPutRequestBuilder toBuilder() =>
      AdminDutySessionsSessionIdBillingBasisPutRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminDutySessionsSessionIdBillingBasisPutRequest &&
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
    return (newBuiltValueToStringHelper(
            r'AdminDutySessionsSessionIdBillingBasisPutRequest')
          ..add('basis', basis)
          ..add('note', note))
        .toString();
  }
}

class AdminDutySessionsSessionIdBillingBasisPutRequestBuilder
    implements
        Builder<AdminDutySessionsSessionIdBillingBasisPutRequest,
            AdminDutySessionsSessionIdBillingBasisPutRequestBuilder> {
  _$AdminDutySessionsSessionIdBillingBasisPutRequest? _$v;

  AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum? _basis;
  AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum? get basis =>
      _$this._basis;
  set basis(AdminDutySessionsSessionIdBillingBasisPutRequestBasisEnum? basis) =>
      _$this._basis = basis;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  AdminDutySessionsSessionIdBillingBasisPutRequestBuilder() {
    AdminDutySessionsSessionIdBillingBasisPutRequest._defaults(this);
  }

  AdminDutySessionsSessionIdBillingBasisPutRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _basis = $v.basis;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminDutySessionsSessionIdBillingBasisPutRequest other) {
    _$v = other as _$AdminDutySessionsSessionIdBillingBasisPutRequest;
  }

  @override
  void update(
      void Function(AdminDutySessionsSessionIdBillingBasisPutRequestBuilder)?
          updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminDutySessionsSessionIdBillingBasisPutRequest build() => _build();

  _$AdminDutySessionsSessionIdBillingBasisPutRequest _build() {
    final _$result = _$v ??
        _$AdminDutySessionsSessionIdBillingBasisPutRequest._(
          basis: BuiltValueNullFieldError.checkNotNull(basis,
              r'AdminDutySessionsSessionIdBillingBasisPutRequest', 'basis'),
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
