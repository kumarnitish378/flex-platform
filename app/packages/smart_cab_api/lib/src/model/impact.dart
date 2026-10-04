//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/impact_affected_requests_inner.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'impact.g.dart';

/// Impact
///
/// Properties:
/// * [affectedRequests] 
/// * [zonesWithoutAvailableVehicle] 
/// * [hardRuleViolations] 
@BuiltValue()
abstract class Impact implements Built<Impact, ImpactBuilder> {
  @BuiltValueField(wireName: r'affected_requests')
  BuiltList<ImpactAffectedRequestsInner>? get affectedRequests;

  @BuiltValueField(wireName: r'zones_without_available_vehicle')
  BuiltList<String>? get zonesWithoutAvailableVehicle;

  @BuiltValueField(wireName: r'hard_rule_violations')
  BuiltList<String>? get hardRuleViolations;

  Impact._();

  factory Impact([void updates(ImpactBuilder b)]) = _$Impact;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ImpactBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<Impact> get serializer => _$ImpactSerializer();
}

class _$ImpactSerializer implements PrimitiveSerializer<Impact> {
  @override
  final Iterable<Type> types = const [Impact, _$Impact];

  @override
  final String wireName = r'Impact';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Impact object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.affectedRequests != null) {
      yield r'affected_requests';
      yield serializers.serialize(
        object.affectedRequests,
        specifiedType: const FullType(BuiltList, [FullType(ImpactAffectedRequestsInner)]),
      );
    }
    if (object.zonesWithoutAvailableVehicle != null) {
      yield r'zones_without_available_vehicle';
      yield serializers.serialize(
        object.zonesWithoutAvailableVehicle,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
    if (object.hardRuleViolations != null) {
      yield r'hard_rule_violations';
      yield serializers.serialize(
        object.hardRuleViolations,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Impact object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ImpactBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'affected_requests':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(ImpactAffectedRequestsInner)]),
          ) as BuiltList<ImpactAffectedRequestsInner>;
          result.affectedRequests.replace(valueDes);
          break;
        case r'zones_without_available_vehicle':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.zonesWithoutAvailableVehicle.replace(valueDes);
          break;
        case r'hard_rule_violations':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.hardRuleViolations.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Impact deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ImpactBuilder();
    final serializedList = (serialized as Iterable<Object?>).toList();
    final unhandled = <Object?>[];
    _deserializeProperties(
      serializers,
      serialized,
      specifiedType: specifiedType,
      serializedList: serializedList,
      unhandled: unhandled,
      result: result,
    );
    return result.build();
  }
}

