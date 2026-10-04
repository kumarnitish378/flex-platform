//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'reason_code.g.dart';

class ReasonCode extends EnumClass {

  @BuiltValueEnumConst(wireName: r'driver_issue')
  static const ReasonCode driverIssue = _$driverIssue;
  @BuiltValueEnumConst(wireName: r'local_knowledge')
  static const ReasonCode localKnowledge = _$localKnowledge;
  @BuiltValueEnumConst(wireName: r'client_request')
  static const ReasonCode clientRequest = _$clientRequest;
  @BuiltValueEnumConst(wireName: r'traffic')
  static const ReasonCode traffic = _$traffic;
  @BuiltValueEnumConst(wireName: r'vehicle_issue')
  static const ReasonCode vehicleIssue = _$vehicleIssue;
  @BuiltValueEnumConst(wireName: r'safety')
  static const ReasonCode safety = _$safety;
  @BuiltValueEnumConst(wireName: r'other')
  static const ReasonCode other = _$other;

  static Serializer<ReasonCode> get serializer => _$reasonCodeSerializer;

  const ReasonCode._(String name): super(name);

  static BuiltSet<ReasonCode> get values => _$values;
  static ReasonCode valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class ReasonCodeMixin = Object with _$ReasonCodeMixin;

