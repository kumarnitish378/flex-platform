//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'simctl_optimizer_put_request.g.dart';

/// SimctlOptimizerPutRequest
///
/// Properties:
/// * [available] 
@BuiltValue()
abstract class SimctlOptimizerPutRequest implements Built<SimctlOptimizerPutRequest, SimctlOptimizerPutRequestBuilder> {
  @BuiltValueField(wireName: r'available')
  bool get available;

  SimctlOptimizerPutRequest._();

  factory SimctlOptimizerPutRequest([void updates(SimctlOptimizerPutRequestBuilder b)]) = _$SimctlOptimizerPutRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SimctlOptimizerPutRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SimctlOptimizerPutRequest> get serializer => _$SimctlOptimizerPutRequestSerializer();
}

class _$SimctlOptimizerPutRequestSerializer implements PrimitiveSerializer<SimctlOptimizerPutRequest> {
  @override
  final Iterable<Type> types = const [SimctlOptimizerPutRequest, _$SimctlOptimizerPutRequest];

  @override
  final String wireName = r'SimctlOptimizerPutRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SimctlOptimizerPutRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'available';
    yield serializers.serialize(
      object.available,
      specifiedType: const FullType(bool),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    SimctlOptimizerPutRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SimctlOptimizerPutRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'available':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.available = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  SimctlOptimizerPutRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SimctlOptimizerPutRequestBuilder();
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

