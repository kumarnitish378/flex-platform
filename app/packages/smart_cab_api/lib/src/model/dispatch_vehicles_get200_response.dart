//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/vehicle_live.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_vehicles_get200_response.g.dart';

/// DispatchVehiclesGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DispatchVehiclesGet200Response implements Built<DispatchVehiclesGet200Response, DispatchVehiclesGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<VehicleLive> get items;

  DispatchVehiclesGet200Response._();

  factory DispatchVehiclesGet200Response([void updates(DispatchVehiclesGet200ResponseBuilder b)]) = _$DispatchVehiclesGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchVehiclesGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchVehiclesGet200Response> get serializer => _$DispatchVehiclesGet200ResponseSerializer();
}

class _$DispatchVehiclesGet200ResponseSerializer implements PrimitiveSerializer<DispatchVehiclesGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchVehiclesGet200Response, _$DispatchVehiclesGet200Response];

  @override
  final String wireName = r'DispatchVehiclesGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchVehiclesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(VehicleLive)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchVehiclesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchVehiclesGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(VehicleLive)]),
          ) as BuiltList<VehicleLive>;
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
  DispatchVehiclesGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchVehiclesGet200ResponseBuilder();
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

