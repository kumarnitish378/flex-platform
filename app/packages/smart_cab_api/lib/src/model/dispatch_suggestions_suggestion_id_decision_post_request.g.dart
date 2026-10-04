// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_suggestions_suggestion_id_decision_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
    _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_approve =
    const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum._(
        'approve');
const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
    _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_chooseOther =
    const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum._(
        'chooseOther');
const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
    _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_reject =
    const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum._(
        'reject');

DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
    _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumValueOf(
        String name) {
  switch (name) {
    case 'approve':
      return _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_approve;
    case 'chooseOther':
      return _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_chooseOther;
    case 'reject':
      return _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_reject;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum>
    _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumValues =
    BuiltSet<
        DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum>(const <DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum>[
  _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_approve,
  _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_chooseOther,
  _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_reject,
]);

Serializer<DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum>
    _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumSerializer =
    _$DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumSerializer();

class _$DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumSerializer
    implements
        PrimitiveSerializer<
            DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum> {
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
    DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
  ];
  @override
  final String wireName =
      'DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum';

  @override
  Object serialize(Serializers serializers,
          DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$DispatchSuggestionsSuggestionIdDecisionPostRequest
    extends DispatchSuggestionsSuggestionIdDecisionPostRequest {
  @override
  final DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum decision;
  @override
  final String? vehicleId;
  @override
  final ReasonCode? reasonCode;

  factory _$DispatchSuggestionsSuggestionIdDecisionPostRequest(
          [void Function(
                  DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder)?
              updates]) =>
      (DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder()
            ..update(updates))
          ._build();

  _$DispatchSuggestionsSuggestionIdDecisionPostRequest._(
      {required this.decision, this.vehicleId, this.reasonCode})
      : super._();
  @override
  DispatchSuggestionsSuggestionIdDecisionPostRequest rebuild(
          void Function(
                  DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder toBuilder() =>
      DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder()
        ..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchSuggestionsSuggestionIdDecisionPostRequest &&
        decision == other.decision &&
        vehicleId == other.vehicleId &&
        reasonCode == other.reasonCode;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, decision.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, reasonCode.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(
            r'DispatchSuggestionsSuggestionIdDecisionPostRequest')
          ..add('decision', decision)
          ..add('vehicleId', vehicleId)
          ..add('reasonCode', reasonCode))
        .toString();
  }
}

class DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder
    implements
        Builder<DispatchSuggestionsSuggestionIdDecisionPostRequest,
            DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder> {
  _$DispatchSuggestionsSuggestionIdDecisionPostRequest? _$v;

  DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum? _decision;
  DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum?
      get decision => _$this._decision;
  set decision(
          DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum?
              decision) =>
      _$this._decision = decision;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  ReasonCode? _reasonCode;
  ReasonCode? get reasonCode => _$this._reasonCode;
  set reasonCode(ReasonCode? reasonCode) => _$this._reasonCode = reasonCode;

  DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder() {
    DispatchSuggestionsSuggestionIdDecisionPostRequest._defaults(this);
  }

  DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _decision = $v.decision;
      _vehicleId = $v.vehicleId;
      _reasonCode = $v.reasonCode;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchSuggestionsSuggestionIdDecisionPostRequest other) {
    _$v = other as _$DispatchSuggestionsSuggestionIdDecisionPostRequest;
  }

  @override
  void update(
      void Function(DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder)?
          updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchSuggestionsSuggestionIdDecisionPostRequest build() => _build();

  _$DispatchSuggestionsSuggestionIdDecisionPostRequest _build() {
    final _$result = _$v ??
        _$DispatchSuggestionsSuggestionIdDecisionPostRequest._(
          decision: BuiltValueNullFieldError.checkNotNull(
              decision,
              r'DispatchSuggestionsSuggestionIdDecisionPostRequest',
              'decision'),
          vehicleId: vehicleId,
          reasonCode: reasonCode,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
