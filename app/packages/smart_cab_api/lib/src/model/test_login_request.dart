//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'test_login_request.g.dart';

/// TestLoginRequest
///
/// Properties:
/// * [phone] 
@BuiltValue()
abstract class TestLoginRequest implements Built<TestLoginRequest, TestLoginRequestBuilder> {
  @BuiltValueField(wireName: r'phone')
  String get phone;

  TestLoginRequest._();

  factory TestLoginRequest([void updates(TestLoginRequestBuilder b)]) = _$TestLoginRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(TestLoginRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<TestLoginRequest> get serializer => _$TestLoginRequestSerializer();
}

class _$TestLoginRequestSerializer implements PrimitiveSerializer<TestLoginRequest> {
  @override
  final Iterable<Type> types = const [TestLoginRequest, _$TestLoginRequest];

  @override
  final String wireName = r'TestLoginRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    TestLoginRequest object, {
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
    TestLoginRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required TestLoginRequestBuilder result,
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
  TestLoginRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = TestLoginRequestBuilder();
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

