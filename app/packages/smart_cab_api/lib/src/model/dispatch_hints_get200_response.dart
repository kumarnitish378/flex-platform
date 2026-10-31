//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/request_hint.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_hints_get200_response.g.dart';

/// DispatchHintsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DispatchHintsGet200Response implements Built<DispatchHintsGet200Response, DispatchHintsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<RequestHint> get items;

  DispatchHintsGet200Response._();

  factory DispatchHintsGet200Response([void updates(DispatchHintsGet200ResponseBuilder b)]) = _$DispatchHintsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchHintsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchHintsGet200Response> get serializer => _$DispatchHintsGet200ResponseSerializer();
}

class _$DispatchHintsGet200ResponseSerializer implements PrimitiveSerializer<DispatchHintsGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchHintsGet200Response, _$DispatchHintsGet200Response];

  @override
  final String wireName = r'DispatchHintsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchHintsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(RequestHint)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchHintsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchHintsGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(RequestHint)]),
          ) as BuiltList<RequestHint>;
          result.items.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DispatchHintsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchHintsGet200ResponseBuilder();
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

