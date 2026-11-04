//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'zone_update.g.dart';

/// Every field optional; omitted fields are left alone.
///
/// Properties:
/// * [name] 
/// * [boundary] 
/// * [active] 
@BuiltValue()
abstract class ZoneUpdate implements Built<ZoneUpdate, ZoneUpdateBuilder> {
  @BuiltValueField(wireName: r'name')
  String? get name;

  @BuiltValueField(wireName: r'boundary')
  BuiltList<LatLng>? get boundary;

  @BuiltValueField(wireName: r'active')
  bool? get active;

  ZoneUpdate._();

  factory ZoneUpdate([void updates(ZoneUpdateBuilder b)]) = _$ZoneUpdate;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ZoneUpdateBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ZoneUpdate> get serializer => _$ZoneUpdateSerializer();
}

class _$ZoneUpdateSerializer implements PrimitiveSerializer<ZoneUpdate> {
  @override
  final Iterable<Type> types = const [ZoneUpdate, _$ZoneUpdate];

  @override
  final String wireName = r'ZoneUpdate';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ZoneUpdate object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.name != null) {
      yield r'name';
      yield serializers.serialize(
        object.name,
        specifiedType: const FullType(String),
      );
    }
    if (object.boundary != null) {
      yield r'boundary';
      yield serializers.serialize(
        object.boundary,
        specifiedType: const FullType(BuiltList, [FullType(LatLng)]),
      );
    }
    if (object.active != null) {
      yield r'active';
      yield serializers.serialize(
        object.active,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ZoneUpdate object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ZoneUpdateBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.name = valueDes;
          break;
        case r'boundary':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(LatLng)]),
          ) as BuiltList<LatLng>;
          result.boundary.replace(valueDes);
          break;
        case r'active':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.active = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ZoneUpdate deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ZoneUpdateBuilder();
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

