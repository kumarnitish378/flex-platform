// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'suggestion.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const SuggestionStatusEnum _$suggestionStatusEnum_offered =
    const SuggestionStatusEnum._('offered');
const SuggestionStatusEnum _$suggestionStatusEnum_accepted =
    const SuggestionStatusEnum._('accepted');
const SuggestionStatusEnum _$suggestionStatusEnum_rejected =
    const SuggestionStatusEnum._('rejected');
const SuggestionStatusEnum _$suggestionStatusEnum_superseded =
    const SuggestionStatusEnum._('superseded');
const SuggestionStatusEnum _$suggestionStatusEnum_expired =
    const SuggestionStatusEnum._('expired');
const SuggestionStatusEnum _$suggestionStatusEnum_failsafeAssigned =
    const SuggestionStatusEnum._('failsafeAssigned');

SuggestionStatusEnum _$suggestionStatusEnumValueOf(String name) {
  switch (name) {
    case 'offered':
      return _$suggestionStatusEnum_offered;
    case 'accepted':
      return _$suggestionStatusEnum_accepted;
    case 'rejected':
      return _$suggestionStatusEnum_rejected;
    case 'superseded':
      return _$suggestionStatusEnum_superseded;
    case 'expired':
      return _$suggestionStatusEnum_expired;
    case 'failsafeAssigned':
      return _$suggestionStatusEnum_failsafeAssigned;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<SuggestionStatusEnum> _$suggestionStatusEnumValues =
    BuiltSet<SuggestionStatusEnum>(const <SuggestionStatusEnum>[
  _$suggestionStatusEnum_offered,
  _$suggestionStatusEnum_accepted,
  _$suggestionStatusEnum_rejected,
  _$suggestionStatusEnum_superseded,
  _$suggestionStatusEnum_expired,
  _$suggestionStatusEnum_failsafeAssigned,
]);

Serializer<SuggestionStatusEnum> _$suggestionStatusEnumSerializer =
    _$SuggestionStatusEnumSerializer();

class _$SuggestionStatusEnumSerializer
    implements PrimitiveSerializer<SuggestionStatusEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'offered': 'offered',
    'accepted': 'accepted',
    'rejected': 'rejected',
    'superseded': 'superseded',
    'expired': 'expired',
    'failsafeAssigned': 'failsafe_assigned',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'offered': 'offered',
    'accepted': 'accepted',
    'rejected': 'rejected',
    'superseded': 'superseded',
    'expired': 'expired',
    'failsafe_assigned': 'failsafeAssigned',
  };

  @override
  final Iterable<Type> types = const <Type>[SuggestionStatusEnum];
  @override
  final String wireName = 'SuggestionStatusEnum';

  @override
  Object serialize(Serializers serializers, SuggestionStatusEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  SuggestionStatusEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      SuggestionStatusEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$Suggestion extends Suggestion {
  @override
  final String? id;
  @override
  final String? requestId;
  @override
  final String? vehicleId;
  @override
  final String? tripId;
  @override
  final int? rank;
  @override
  final num? cost;
  @override
  final BuiltList<String>? reasons;
  @override
  final SuggestionStatusEnum? status;
  @override
  final DateTime? offeredAt;
  @override
  final DateTime? failsafeDueAt;
  @override
  final DateTime? escalatedAt;
  @override
  final DateTime? decidedAt;

  factory _$Suggestion([void Function(SuggestionBuilder)? updates]) =>
      (SuggestionBuilder()..update(updates))._build();

  _$Suggestion._(
      {this.id,
      this.requestId,
      this.vehicleId,
      this.tripId,
      this.rank,
      this.cost,
      this.reasons,
      this.status,
      this.offeredAt,
      this.failsafeDueAt,
      this.escalatedAt,
      this.decidedAt})
      : super._();
  @override
  Suggestion rebuild(void Function(SuggestionBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SuggestionBuilder toBuilder() => SuggestionBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Suggestion &&
        id == other.id &&
        requestId == other.requestId &&
        vehicleId == other.vehicleId &&
        tripId == other.tripId &&
        rank == other.rank &&
        cost == other.cost &&
        reasons == other.reasons &&
        status == other.status &&
        offeredAt == other.offeredAt &&
        failsafeDueAt == other.failsafeDueAt &&
        escalatedAt == other.escalatedAt &&
        decidedAt == other.decidedAt;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, rank.hashCode);
    _$hash = $jc(_$hash, cost.hashCode);
    _$hash = $jc(_$hash, reasons.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, offeredAt.hashCode);
    _$hash = $jc(_$hash, failsafeDueAt.hashCode);
    _$hash = $jc(_$hash, escalatedAt.hashCode);
    _$hash = $jc(_$hash, decidedAt.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Suggestion')
          ..add('id', id)
          ..add('requestId', requestId)
          ..add('vehicleId', vehicleId)
          ..add('tripId', tripId)
          ..add('rank', rank)
          ..add('cost', cost)
          ..add('reasons', reasons)
          ..add('status', status)
          ..add('offeredAt', offeredAt)
          ..add('failsafeDueAt', failsafeDueAt)
          ..add('escalatedAt', escalatedAt)
          ..add('decidedAt', decidedAt))
        .toString();
  }
}

class SuggestionBuilder implements Builder<Suggestion, SuggestionBuilder> {
  _$Suggestion? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  int? _rank;
  int? get rank => _$this._rank;
  set rank(int? rank) => _$this._rank = rank;

  num? _cost;
  num? get cost => _$this._cost;
  set cost(num? cost) => _$this._cost = cost;

  ListBuilder<String>? _reasons;
  ListBuilder<String> get reasons => _$this._reasons ??= ListBuilder<String>();
  set reasons(ListBuilder<String>? reasons) => _$this._reasons = reasons;

  SuggestionStatusEnum? _status;
  SuggestionStatusEnum? get status => _$this._status;
  set status(SuggestionStatusEnum? status) => _$this._status = status;

  DateTime? _offeredAt;
  DateTime? get offeredAt => _$this._offeredAt;
  set offeredAt(DateTime? offeredAt) => _$this._offeredAt = offeredAt;

  DateTime? _failsafeDueAt;
  DateTime? get failsafeDueAt => _$this._failsafeDueAt;
  set failsafeDueAt(DateTime? failsafeDueAt) =>
      _$this._failsafeDueAt = failsafeDueAt;

  DateTime? _escalatedAt;
  DateTime? get escalatedAt => _$this._escalatedAt;
  set escalatedAt(DateTime? escalatedAt) => _$this._escalatedAt = escalatedAt;

  DateTime? _decidedAt;
  DateTime? get decidedAt => _$this._decidedAt;
  set decidedAt(DateTime? decidedAt) => _$this._decidedAt = decidedAt;

  SuggestionBuilder() {
    Suggestion._defaults(this);
  }

  SuggestionBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _requestId = $v.requestId;
      _vehicleId = $v.vehicleId;
      _tripId = $v.tripId;
      _rank = $v.rank;
      _cost = $v.cost;
      _reasons = $v.reasons?.toBuilder();
      _status = $v.status;
      _offeredAt = $v.offeredAt;
      _failsafeDueAt = $v.failsafeDueAt;
      _escalatedAt = $v.escalatedAt;
      _decidedAt = $v.decidedAt;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(Suggestion other) {
    _$v = other as _$Suggestion;
  }

  @override
  void update(void Function(SuggestionBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Suggestion build() => _build();

  _$Suggestion _build() {
    _$Suggestion _$result;
    try {
      _$result = _$v ??
          _$Suggestion._(
            id: id,
            requestId: requestId,
            vehicleId: vehicleId,
            tripId: tripId,
            rank: rank,
            cost: cost,
            reasons: _reasons?.build(),
            status: status,
            offeredAt: offeredAt,
            failsafeDueAt: failsafeDueAt,
            escalatedAt: escalatedAt,
            decidedAt: decidedAt,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'reasons';
        _reasons?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'Suggestion', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
