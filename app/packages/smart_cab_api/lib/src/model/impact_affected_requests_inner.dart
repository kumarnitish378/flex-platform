//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'impact_affected_requests_inner.g.dart';

/// ImpactAffectedRequestsInner
///
/// Properties:
/// * [requestId] 
/// * [etaChangeMinutes] 
@BuiltValue()
abstract class ImpactAffectedRequestsInner implements Built<ImpactAffectedRequestsInner, ImpactAffectedRequestsInnerBuilder> {
  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'eta_change_minutes')
  num? get etaChangeMinutes;

  ImpactAffectedRequestsInner._();

  factory ImpactAffectedRequestsInner([void updates(ImpactAffectedRequestsInnerBuilder b)]) = _$ImpactAffectedRequestsInner;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ImpactAffectedRequestsInnerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ImpactAffectedRequestsInner> get serializer => _$ImpactAffectedRequestsInnerSerializer();
}

class _$ImpactAffectedRequestsInnerSerializer implements PrimitiveSerializer<ImpactAffectedRequestsInner> {
  @override
  final Iterable<Type> types = const [ImpactAffectedRequestsInner, _$ImpactAffectedRequestsInner];

  @override
  final String wireName = r'ImpactAffectedRequestsInner';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ImpactAffectedRequestsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType(String),
      );
    }
    if (object.etaChangeMinutes != null) {
      yield r'eta_change_minutes';
      yield serializers.serialize(
        object.etaChangeMinutes,
        specifiedType: const FullType(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ImpactAffectedRequestsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ImpactAffectedRequestsInnerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'request_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.requestId = valueDes;
          break;
        case r'eta_change_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.etaChangeMinutes = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ImpactAffectedRequestsInner deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ImpactAffectedRequestsInnerBuilder();
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

