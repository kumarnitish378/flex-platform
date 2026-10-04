//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'otp_request.g.dart';

/// OtpRequest
///
/// Properties:
/// * [phone] 
@BuiltValue()
abstract class OtpRequest implements Built<OtpRequest, OtpRequestBuilder> {
  @BuiltValueField(wireName: r'phone')
  String get phone;

  OtpRequest._();

  factory OtpRequest([void updates(OtpRequestBuilder b)]) = _$OtpRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OtpRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OtpRequest> get serializer => _$OtpRequestSerializer();
}

class _$OtpRequestSerializer implements PrimitiveSerializer<OtpRequest> {
  @override
  final Iterable<Type> types = const [OtpRequest, _$OtpRequest];

  @override
  final String wireName = r'OtpRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OtpRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'phone';
    yield serializers.serialize(
      object.phone,
      specifiedType: const FullType(String),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    OtpRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OtpRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.phone = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OtpRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OtpRequestBuilder();
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

