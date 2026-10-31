//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/impact.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'override_result.g.dart';

/// OverrideResult
///
/// Properties:
/// * [overrideId] 
/// * [impact] 
/// * [expiresAt] - When this override lapses. Null means it stands until the trip ends.
/// * [tripId] - The trip the request ended up on, for reassign.
@BuiltValue()
abstract class OverrideResult implements Built<OverrideResult, OverrideResultBuilder> {
  @BuiltValueField(wireName: r'override_id')
  String? get overrideId;

  @BuiltValueField(wireName: r'impact')
  Impact? get impact;

  /// When this override lapses. Null means it stands until the trip ends.
  @BuiltValueField(wireName: r'expires_at')
  DateTime? get expiresAt;

  /// The trip the request ended up on, for reassign.
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  OverrideResult._();

  factory OverrideResult([void updates(OverrideResultBuilder b)]) = _$OverrideResult;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OverrideResultBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OverrideResult> get serializer => _$OverrideResultSerializer();
}

class _$OverrideResultSerializer implements PrimitiveSerializer<OverrideResult> {
  @override
  final Iterable<Type> types = const [OverrideResult, _$OverrideResult];

  @override
  final String wireName = r'OverrideResult';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OverrideResult object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.overrideId != null) {
      yield r'override_id';
      yield serializers.serialize(
        object.overrideId,
        specifiedType: const FullType(String),
      );
    }
    if (object.impact != null) {
      yield r'impact';
      yield serializers.serialize(
        object.impact,
        specifiedType: const FullType(Impact),
      );
    }
    if (object.expiresAt != null) {
      yield r'expires_at';
      yield serializers.serialize(
        object.expiresAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OverrideResult object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OverrideResultBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'override_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.overrideId = valueDes;
          break;
        case r'impact':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Impact),
          ) as Impact;
          result.impact.replace(valueDes);
          break;
        case r'expires_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.expiresAt = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OverrideResult deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OverrideResultBuilder();
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

