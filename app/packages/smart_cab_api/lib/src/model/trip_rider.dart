//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'trip_rider.g.dart';

/// TripRider
///
/// Properties:
/// * [requestId] 
/// * [riderFirstName] 
/// * [addedMinutes] - minutes beyond riding alone
@BuiltValue()
abstract class TripRider implements Built<TripRider, TripRiderBuilder> {
  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'rider_first_name')
  String? get riderFirstName;

  /// minutes beyond riding alone
  @BuiltValueField(wireName: r'added_minutes')
  num? get addedMinutes;

  TripRider._();

  factory TripRider([void updates(TripRiderBuilder b)]) = _$TripRider;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(TripRiderBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<TripRider> get serializer => _$TripRiderSerializer();
}

class _$TripRiderSerializer implements PrimitiveSerializer<TripRider> {
  @override
  final Iterable<Type> types = const [TripRider, _$TripRider];

  @override
  final String wireName = r'TripRider';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    TripRider object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType(String),
      );
    }
    if (object.riderFirstName != null) {
      yield r'rider_first_name';
      yield serializers.serialize(
        object.riderFirstName,
        specifiedType: const FullType(String),
      );
    }
    if (object.addedMinutes != null) {
      yield r'added_minutes';
      yield serializers.serialize(
        object.addedMinutes,
        specifiedType: const FullType.nullable(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    TripRider object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required TripRiderBuilder result,
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
        case r'rider_first_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.riderFirstName = valueDes;
          break;
        case r'added_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.addedMinutes = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  TripRider deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = TripRiderBuilder();
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

