//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/suggestion.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_suggestions_get200_response.g.dart';

/// DispatchSuggestionsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DispatchSuggestionsGet200Response implements Built<DispatchSuggestionsGet200Response, DispatchSuggestionsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Suggestion>? get items;

  DispatchSuggestionsGet200Response._();

  factory DispatchSuggestionsGet200Response([void updates(DispatchSuggestionsGet200ResponseBuilder b)]) = _$DispatchSuggestionsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchSuggestionsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchSuggestionsGet200Response> get serializer => _$DispatchSuggestionsGet200ResponseSerializer();
}

class _$DispatchSuggestionsGet200ResponseSerializer implements PrimitiveSerializer<DispatchSuggestionsGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchSuggestionsGet200Response, _$DispatchSuggestionsGet200Response];

  @override
  final String wireName = r'DispatchSuggestionsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchSuggestionsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(Suggestion)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchSuggestionsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchSuggestionsGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Suggestion)]),
          ) as BuiltList<Suggestion>;
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
  DispatchSuggestionsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchSuggestionsGet200ResponseBuilder();
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

