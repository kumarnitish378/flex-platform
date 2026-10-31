//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/alert.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'alerts_get200_response.g.dart';

/// AlertsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class AlertsGet200Response implements Built<AlertsGet200Response, AlertsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Alert> get items;

  AlertsGet200Response._();

  factory AlertsGet200Response([void updates(AlertsGet200ResponseBuilder b)]) = _$AlertsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AlertsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AlertsGet200Response> get serializer => _$AlertsGet200ResponseSerializer();
}

class _$AlertsGet200ResponseSerializer implements PrimitiveSerializer<AlertsGet200Response> {
  @override
  final Iterable<Type> types = const [AlertsGet200Response, _$AlertsGet200Response];

  @override
  final String wireName = r'AlertsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AlertsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(Alert)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    AlertsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AlertsGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Alert)]),
          ) as BuiltList<Alert>;
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
  AlertsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AlertsGet200ResponseBuilder();
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

