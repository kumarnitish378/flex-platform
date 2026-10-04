// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'reason_code.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const ReasonCode _$driverIssue = const ReasonCode._('driverIssue');
const ReasonCode _$localKnowledge = const ReasonCode._('localKnowledge');
const ReasonCode _$clientRequest = const ReasonCode._('clientRequest');
const ReasonCode _$traffic = const ReasonCode._('traffic');
const ReasonCode _$vehicleIssue = const ReasonCode._('vehicleIssue');
const ReasonCode _$safety = const ReasonCode._('safety');
const ReasonCode _$other = const ReasonCode._('other');

ReasonCode _$valueOf(String name) {
  switch (name) {
    case 'driverIssue':
      return _$driverIssue;
    case 'localKnowledge':
      return _$localKnowledge;
    case 'clientRequest':
      return _$clientRequest;
    case 'traffic':
      return _$traffic;
    case 'vehicleIssue':
      return _$vehicleIssue;
    case 'safety':
      return _$safety;
    case 'other':
      return _$other;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<ReasonCode> _$values = BuiltSet<ReasonCode>(const <ReasonCode>[
  _$driverIssue,
  _$localKnowledge,
  _$clientRequest,
  _$traffic,
  _$vehicleIssue,
  _$safety,
  _$other,
]);

class _$ReasonCodeMeta {
  const _$ReasonCodeMeta();
  ReasonCode get driverIssue => _$driverIssue;
  ReasonCode get localKnowledge => _$localKnowledge;
  ReasonCode get clientRequest => _$clientRequest;
  ReasonCode get traffic => _$traffic;
  ReasonCode get vehicleIssue => _$vehicleIssue;
  ReasonCode get safety => _$safety;
  ReasonCode get other => _$other;
  ReasonCode valueOf(String name) => _$valueOf(name);
  BuiltSet<ReasonCode> get values => _$values;
}

abstract class _$ReasonCodeMixin {
  // ignore: non_constant_identifier_names
  _$ReasonCodeMeta get ReasonCode => const _$ReasonCodeMeta();
}

Serializer<ReasonCode> _$reasonCodeSerializer = _$ReasonCodeSerializer();

class _$ReasonCodeSerializer implements PrimitiveSerializer<ReasonCode> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'driverIssue': 'driver_issue',
    'localKnowledge': 'local_knowledge',
    'clientRequest': 'client_request',
    'traffic': 'traffic',
    'vehicleIssue': 'vehicle_issue',
    'safety': 'safety',
    'other': 'other',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'driver_issue': 'driverIssue',
    'local_knowledge': 'localKnowledge',
    'client_request': 'clientRequest',
    'traffic': 'traffic',
    'vehicle_issue': 'vehicleIssue',
    'safety': 'safety',
    'other': 'other',
  };

  @override
  final Iterable<Type> types = const <Type>[ReasonCode];
  @override
  final String wireName = 'ReasonCode';

  @override
  Object serialize(Serializers serializers, ReasonCode object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  ReasonCode deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      ReasonCode.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
