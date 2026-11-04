//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/zone_input.dart';
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'zone.g.dart';

/// Zone
///
/// Properties:
/// * [name] 
/// * [boundary] - The outer ring, in order. Send it open or closed - the last point is joined to the first either way. A ring that crosses itself is refused with 422 rather than being silently repaired, because the repair is a guess about which lobe the operator meant. 
/// * [active] 
/// * [id] 
/// * [employeeCount] - Employees whose home falls in this zone. An inactive zone covers nobody and reports zero - which is the point of deactivating one. 
@BuiltValue()
abstract class Zone implements ZoneInput, Built<Zone, ZoneBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  /// Employees whose home falls in this zone. An inactive zone covers nobody and reports zero - which is the point of deactivating one. 
  @BuiltValueField(wireName: r'employee_count')
  int? get employeeCount;

  Zone._();

  factory Zone([void updates(ZoneBuilder b)]) = _$Zone;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ZoneBuilder b) => b
      ..active = true;

  @BuiltValueSerializer(custom: true)
  static Serializer<Zone> get serializer => _$ZoneSerializer();
}

class _$ZoneSerializer implements PrimitiveSerializer<Zone> {
  @override
  final Iterable<Type> types = const [Zone, _$Zone];

  @override
  final String wireName = r'Zone';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Zone object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'boundary';
    yield serializers.serialize(
      object.boundary,
      specifiedType: const FullType(BuiltList, [FullType(LatLng)]),
    );
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    if (object.active != null) {
      yield r'active';
      yield serializers.serialize(
        object.active,
        specifiedType: const FullType(bool),
      );
    }
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.employeeCount != null) {
      yield r'employee_count';
      yield serializers.serialize(
        object.employeeCount,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Zone object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ZoneBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'boundary':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(LatLng)]),
          ) as BuiltList<LatLng>;
          result.boundary.replace(valueDes);
          break;
        case r'name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.name = valueDes;
          break;
        case r'active':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.active = valueDes;
          break;
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'employee_count':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.employeeCount = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Zone deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ZoneBuilder();
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

