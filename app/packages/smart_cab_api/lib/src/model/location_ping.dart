//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'location_ping.g.dart';

/// LocationPing
///
/// Properties:
/// * [ts] 
/// * [lat] 
/// * [lng] 
/// * [speedMps] 
/// * [headingDeg] 
/// * [accuracyM] 
/// * [batteryPct] 
@BuiltValue()
abstract class LocationPing implements Built<LocationPing, LocationPingBuilder> {
  @BuiltValueField(wireName: r'ts')
  DateTime get ts;

  @BuiltValueField(wireName: r'lat')
  num get lat;

  @BuiltValueField(wireName: r'lng')
  num get lng;

  @BuiltValueField(wireName: r'speed_mps')
  num? get speedMps;

  @BuiltValueField(wireName: r'heading_deg')
  num? get headingDeg;

  @BuiltValueField(wireName: r'accuracy_m')
  num? get accuracyM;

  @BuiltValueField(wireName: r'battery_pct')
  int? get batteryPct;

  LocationPing._();

  factory LocationPing([void updates(LocationPingBuilder b)]) = _$LocationPing;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(LocationPingBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<LocationPing> get serializer => _$LocationPingSerializer();
}

class _$LocationPingSerializer implements PrimitiveSerializer<LocationPing> {
  @override
  final Iterable<Type> types = const [LocationPing, _$LocationPing];

  @override
  final String wireName = r'LocationPing';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    LocationPing object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'ts';
    yield serializers.serialize(
      object.ts,
      specifiedType: const FullType(DateTime),
    );
    yield r'lat';
    yield serializers.serialize(
      object.lat,
      specifiedType: const FullType(num),
    );
    yield r'lng';
    yield serializers.serialize(
      object.lng,
      specifiedType: const FullType(num),
    );
    if (object.speedMps != null) {
      yield r'speed_mps';
      yield serializers.serialize(
        object.speedMps,
        specifiedType: const FullType(num),
      );
    }
    if (object.headingDeg != null) {
      yield r'heading_deg';
      yield serializers.serialize(
        object.headingDeg,
        specifiedType: const FullType(num),
      );
    }
    if (object.accuracyM != null) {
      yield r'accuracy_m';
      yield serializers.serialize(
        object.accuracyM,
        specifiedType: const FullType(num),
      );
    }
    if (object.batteryPct != null) {
      yield r'battery_pct';
      yield serializers.serialize(
        object.batteryPct,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    LocationPing object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required LocationPingBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'ts':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.ts = valueDes;
          break;
        case r'lat':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.lat = valueDes;
          break;
        case r'lng':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.lng = valueDes;
          break;
        case r'speed_mps':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.speedMps = valueDes;
          break;
        case r'heading_deg':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.headingDeg = valueDes;
          break;
        case r'accuracy_m':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.accuracyM = valueDes;
          break;
        case r'battery_pct':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.batteryPct = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  LocationPing deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = LocationPingBuilder();
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

