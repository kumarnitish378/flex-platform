//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'driver_issues_post_request.g.dart';

/// DriverIssuesPostRequest
///
/// Properties:
/// * [type] 
/// * [note] 
/// * [tripId] 
/// * [lat] 
/// * [lng] 
@BuiltValue()
abstract class DriverIssuesPostRequest implements Built<DriverIssuesPostRequest, DriverIssuesPostRequestBuilder> {
  @BuiltValueField(wireName: r'type')
  DriverIssuesPostRequestTypeEnum get type;
  // enum typeEnum {  breakdown,  accident,  traffic_block,  rider_issue,  other,  };

  @BuiltValueField(wireName: r'note')
  String? get note;

  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'lat')
  num? get lat;

  @BuiltValueField(wireName: r'lng')
  num? get lng;

  DriverIssuesPostRequest._();

  factory DriverIssuesPostRequest([void updates(DriverIssuesPostRequestBuilder b)]) = _$DriverIssuesPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DriverIssuesPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DriverIssuesPostRequest> get serializer => _$DriverIssuesPostRequestSerializer();
}

class _$DriverIssuesPostRequestSerializer implements PrimitiveSerializer<DriverIssuesPostRequest> {
  @override
  final Iterable<Type> types = const [DriverIssuesPostRequest, _$DriverIssuesPostRequest];

  @override
  final String wireName = r'DriverIssuesPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DriverIssuesPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'type';
    yield serializers.serialize(
      object.type,
      specifiedType: const FullType(DriverIssuesPostRequestTypeEnum),
    );
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType(String),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.lat != null) {
      yield r'lat';
      yield serializers.serialize(
        object.lat,
        specifiedType: const FullType(num),
      );
    }
    if (object.lng != null) {
      yield r'lng';
      yield serializers.serialize(
        object.lng,
        specifiedType: const FullType(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DriverIssuesPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DriverIssuesPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DriverIssuesPostRequestTypeEnum),
          ) as DriverIssuesPostRequestTypeEnum;
          result.type = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.note = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
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
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DriverIssuesPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DriverIssuesPostRequestBuilder();
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

class DriverIssuesPostRequestTypeEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'breakdown')
  static const DriverIssuesPostRequestTypeEnum breakdown = _$driverIssuesPostRequestTypeEnum_breakdown;
  @BuiltValueEnumConst(wireName: r'accident')
  static const DriverIssuesPostRequestTypeEnum accident = _$driverIssuesPostRequestTypeEnum_accident;
  @BuiltValueEnumConst(wireName: r'traffic_block')
  static const DriverIssuesPostRequestTypeEnum trafficBlock = _$driverIssuesPostRequestTypeEnum_trafficBlock;
  @BuiltValueEnumConst(wireName: r'rider_issue')
  static const DriverIssuesPostRequestTypeEnum riderIssue = _$driverIssuesPostRequestTypeEnum_riderIssue;
  @BuiltValueEnumConst(wireName: r'other')
  static const DriverIssuesPostRequestTypeEnum other = _$driverIssuesPostRequestTypeEnum_other;

  static Serializer<DriverIssuesPostRequestTypeEnum> get serializer => _$driverIssuesPostRequestTypeEnumSerializer;

  const DriverIssuesPostRequestTypeEnum._(String name): super(name);

  static BuiltSet<DriverIssuesPostRequestTypeEnum> get values => _$driverIssuesPostRequestTypeEnumValues;
  static DriverIssuesPostRequestTypeEnum valueOf(String name) => _$driverIssuesPostRequestTypeEnumValueOf(name);
}

