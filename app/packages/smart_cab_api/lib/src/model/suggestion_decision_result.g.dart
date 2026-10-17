// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'suggestion_decision_result.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const SuggestionDecisionResultDecisionEnum
    _$suggestionDecisionResultDecisionEnum_approve =
    const SuggestionDecisionResultDecisionEnum._('approve');
const SuggestionDecisionResultDecisionEnum
    _$suggestionDecisionResultDecisionEnum_chooseOther =
    const SuggestionDecisionResultDecisionEnum._('chooseOther');
const SuggestionDecisionResultDecisionEnum
    _$suggestionDecisionResultDecisionEnum_reject =
    const SuggestionDecisionResultDecisionEnum._('reject');

SuggestionDecisionResultDecisionEnum
    _$suggestionDecisionResultDecisionEnumValueOf(String name) {
  switch (name) {
    case 'approve':
      return _$suggestionDecisionResultDecisionEnum_approve;
    case 'chooseOther':
      return _$suggestionDecisionResultDecisionEnum_chooseOther;
    case 'reject':
      return _$suggestionDecisionResultDecisionEnum_reject;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<SuggestionDecisionResultDecisionEnum>
    _$suggestionDecisionResultDecisionEnumValues = BuiltSet<
        SuggestionDecisionResultDecisionEnum>(const <SuggestionDecisionResultDecisionEnum>[
  _$suggestionDecisionResultDecisionEnum_approve,
  _$suggestionDecisionResultDecisionEnum_chooseOther,
  _$suggestionDecisionResultDecisionEnum_reject,
]);

const SuggestionDecisionResultStatusEnum
    _$suggestionDecisionResultStatusEnum_accepted =
    const SuggestionDecisionResultStatusEnum._('accepted');
const SuggestionDecisionResultStatusEnum
    _$suggestionDecisionResultStatusEnum_rejected =
    const SuggestionDecisionResultStatusEnum._('rejected');
const SuggestionDecisionResultStatusEnum
    _$suggestionDecisionResultStatusEnum_superseded =
    const SuggestionDecisionResultStatusEnum._('superseded');
const SuggestionDecisionResultStatusEnum
    _$suggestionDecisionResultStatusEnum_expired =
    const SuggestionDecisionResultStatusEnum._('expired');
const SuggestionDecisionResultStatusEnum
    _$suggestionDecisionResultStatusEnum_offered =
    const SuggestionDecisionResultStatusEnum._('offered');

SuggestionDecisionResultStatusEnum _$suggestionDecisionResultStatusEnumValueOf(
    String name) {
  switch (name) {
    case 'accepted':
      return _$suggestionDecisionResultStatusEnum_accepted;
    case 'rejected':
      return _$suggestionDecisionResultStatusEnum_rejected;
    case 'superseded':
      return _$suggestionDecisionResultStatusEnum_superseded;
    case 'expired':
      return _$suggestionDecisionResultStatusEnum_expired;
    case 'offered':
      return _$suggestionDecisionResultStatusEnum_offered;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<SuggestionDecisionResultStatusEnum>
    _$suggestionDecisionResultStatusEnumValues = BuiltSet<
        SuggestionDecisionResultStatusEnum>(const <SuggestionDecisionResultStatusEnum>[
  _$suggestionDecisionResultStatusEnum_accepted,
  _$suggestionDecisionResultStatusEnum_rejected,
  _$suggestionDecisionResultStatusEnum_superseded,
  _$suggestionDecisionResultStatusEnum_expired,
  _$suggestionDecisionResultStatusEnum_offered,
]);

Serializer<SuggestionDecisionResultDecisionEnum>
    _$suggestionDecisionResultDecisionEnumSerializer =
    _$SuggestionDecisionResultDecisionEnumSerializer();
Serializer<SuggestionDecisionResultStatusEnum>
    _$suggestionDecisionResultStatusEnumSerializer =
    _$SuggestionDecisionResultStatusEnumSerializer();

class _$SuggestionDecisionResultDecisionEnumSerializer
    implements PrimitiveSerializer<SuggestionDecisionResultDecisionEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'approve': 'approve',
    'chooseOther': 'choose_other',
    'reject': 'reject',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'approve': 'approve',
    'choose_other': 'chooseOther',
    'reject': 'reject',
  };

  @override
  final Iterable<Type> types = const <Type>[
    SuggestionDecisionResultDecisionEnum
  ];
  @override
  final String wireName = 'SuggestionDecisionResultDecisionEnum';

  @override
  Object serialize(
          Serializers serializers, SuggestionDecisionResultDecisionEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  SuggestionDecisionResultDecisionEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      SuggestionDecisionResultDecisionEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$SuggestionDecisionResultStatusEnumSerializer
    implements PrimitiveSerializer<SuggestionDecisionResultStatusEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'accepted': 'accepted',
    'rejected': 'rejected',
    'superseded': 'superseded',
    'expired': 'expired',
    'offered': 'offered',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'accepted': 'accepted',
    'rejected': 'rejected',
    'superseded': 'superseded',
    'expired': 'expired',
    'offered': 'offered',
  };

  @override
  final Iterable<Type> types = const <Type>[SuggestionDecisionResultStatusEnum];
  @override
  final String wireName = 'SuggestionDecisionResultStatusEnum';

  @override
  Object serialize(
          Serializers serializers, SuggestionDecisionResultStatusEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  SuggestionDecisionResultStatusEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      SuggestionDecisionResultStatusEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$SuggestionDecisionResult extends SuggestionDecisionResult {
  @override
  final String? suggestionId;
  @override
  final SuggestionDecisionResultDecisionEnum? decision;
  @override
  final SuggestionDecisionResultStatusEnum? status;
  @override
  final String? tripId;

  factory _$SuggestionDecisionResult(
          [void Function(SuggestionDecisionResultBuilder)? updates]) =>
      (SuggestionDecisionResultBuilder()..update(updates))._build();

  _$SuggestionDecisionResult._(
      {this.suggestionId, this.decision, this.status, this.tripId})
      : super._();
  @override
  SuggestionDecisionResult rebuild(
          void Function(SuggestionDecisionResultBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SuggestionDecisionResultBuilder toBuilder() =>
      SuggestionDecisionResultBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SuggestionDecisionResult &&
        suggestionId == other.suggestionId &&
        decision == other.decision &&
        status == other.status &&
        tripId == other.tripId;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, suggestionId.hashCode);
    _$hash = $jc(_$hash, decision.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SuggestionDecisionResult')
          ..add('suggestionId', suggestionId)
          ..add('decision', decision)
          ..add('status', status)
          ..add('tripId', tripId))
        .toString();
  }
}

class SuggestionDecisionResultBuilder
    implements
        Builder<SuggestionDecisionResult, SuggestionDecisionResultBuilder> {
  _$SuggestionDecisionResult? _$v;

  String? _suggestionId;
  String? get suggestionId => _$this._suggestionId;
  set suggestionId(String? suggestionId) => _$this._suggestionId = suggestionId;

  SuggestionDecisionResultDecisionEnum? _decision;
  SuggestionDecisionResultDecisionEnum? get decision => _$this._decision;
  set decision(SuggestionDecisionResultDecisionEnum? decision) =>
      _$this._decision = decision;

  SuggestionDecisionResultStatusEnum? _status;
  SuggestionDecisionResultStatusEnum? get status => _$this._status;
  set status(SuggestionDecisionResultStatusEnum? status) =>
      _$this._status = status;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  SuggestionDecisionResultBuilder() {
    SuggestionDecisionResult._defaults(this);
  }

  SuggestionDecisionResultBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _suggestionId = $v.suggestionId;
      _decision = $v.decision;
      _status = $v.status;
      _tripId = $v.tripId;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SuggestionDecisionResult other) {
    _$v = other as _$SuggestionDecisionResult;
  }

  @override
  void update(void Function(SuggestionDecisionResultBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SuggestionDecisionResult build() => _build();

  _$SuggestionDecisionResult _build() {
    final _$result = _$v ??
        _$SuggestionDecisionResult._(
          suggestionId: suggestionId,
          decision: decision,
          status: status,
          tripId: tripId,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
