//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'auth_refresh_post_request.g.dart';

/// AuthRefreshPostRequest
///
/// Properties:
/// * [refreshToken] 
@BuiltValue()
abstract class AuthRefreshPostRequest implements Built<AuthRefreshPostRequest, AuthRefreshPostRequestBuilder> {
  @BuiltValueField(wireName: r'refresh_token')
  String get refreshToken;

  AuthRefreshPostRequest._();

  factory AuthRefreshPostRequest([void updates(AuthRefreshPostRequestBuilder b)]) = _$AuthRefreshPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AuthRefreshPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AuthRefreshPostRequest> get serializer => _$AuthRefreshPostRequestSerializer();
}

class _$AuthRefreshPostRequestSerializer implements PrimitiveSerializer<AuthRefreshPostRequest> {
  @override
  final Iterable<Type> types = const [AuthRefreshPostRequest, _$AuthRefreshPostRequest];

  @override
  final String wireName = r'AuthRefreshPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AuthRefreshPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'refresh_token';
    yield serializers.serialize(
      object.refreshToken,
      specifiedType: const FullType(String),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    AuthRefreshPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AuthRefreshPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'refresh_token':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.refreshToken = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  AuthRefreshPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AuthRefreshPostRequestBuilder();
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

