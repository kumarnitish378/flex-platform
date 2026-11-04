//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/reason_code.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_assign_post_request.g.dart';

/// DispatchAssignPostRequest
///
/// Properties:
/// * [requestId] 
/// * [vehicleId] 
/// * [tripId] - add to this existing trip
/// * [reasonCode] 
/// * [note] 
@BuiltValue()
abstract class DispatchAssignPostRequest implements Built<DispatchAssignPostRequest, DispatchAssignPostRequestBuilder> {
  @BuiltValueField(wireName: r'request_id')
  String get requestId;

  @BuiltValueField(wireName: r'vehicle_id')
  String get vehicleId;

  /// add to this existing trip
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'reason_code')
  ReasonCode? get reasonCode;
  // enum reasonCodeEnum {  driver_issue,  local_knowledge,  client_request,  traffic,  vehicle_issue,  safety,  other,  };

  @BuiltValueField(wireName: r'note')
  String? get note;

  DispatchAssignPostRequest._();

  factory DispatchAssignPostRequest([void updates(DispatchAssignPostRequestBuilder b)]) = _$DispatchAssignPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchAssignPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchAssignPostRequest> get serializer => _$DispatchAssignPostRequestSerializer();
}

class _$DispatchAssignPostRequestSerializer implements PrimitiveSerializer<DispatchAssignPostRequest> {
  @override
  final Iterable<Type> types = const [DispatchAssignPostRequest, _$DispatchAssignPostRequest];

  @override
  final String wireName = r'DispatchAssignPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchAssignPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'request_id';
    yield serializers.serialize(
      object.requestId,
      specifiedType: const FullType(String),
    );
    yield r'vehicle_id';
    yield serializers.serialize(
      object.vehicleId,
      specifiedType: const FullType(String),
    );
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.reasonCode != null) {
      yield r'reason_code';
      yield serializers.serialize(
        object.reasonCode,
        specifiedType: const FullType(ReasonCode),
      );
    }
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchAssignPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchAssignPostRequestBuilder result,
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
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.vehicleId = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        case r'reason_code':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ReasonCode),
          ) as ReasonCode;
          result.reasonCode = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.note = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DispatchAssignPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchAssignPostRequestBuilder();
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

