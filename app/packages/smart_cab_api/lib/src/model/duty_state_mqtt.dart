//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'duty_state_mqtt.g.dart';

/// DutyStateMqtt
///
/// Properties:
/// * [host] 
/// * [port] 
/// * [username] 
/// * [password] 
/// * [topicPrefix] 
@BuiltValue()
abstract class DutyStateMqtt implements Built<DutyStateMqtt, DutyStateMqttBuilder> {
  @BuiltValueField(wireName: r'host')
  String? get host;

  @BuiltValueField(wireName: r'port')
  int? get port;

  @BuiltValueField(wireName: r'username')
  String? get username;

  @BuiltValueField(wireName: r'password')
  String? get password;

  @BuiltValueField(wireName: r'topic_prefix')
  String? get topicPrefix;

  DutyStateMqtt._();

  factory DutyStateMqtt([void updates(DutyStateMqttBuilder b)]) = _$DutyStateMqtt;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DutyStateMqttBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DutyStateMqtt> get serializer => _$DutyStateMqttSerializer();
}

class _$DutyStateMqttSerializer implements PrimitiveSerializer<DutyStateMqtt> {
  @override
  final Iterable<Type> types = const [DutyStateMqtt, _$DutyStateMqtt];

  @override
  final String wireName = r'DutyStateMqtt';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DutyStateMqtt object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.host != null) {
      yield r'host';
      yield serializers.serialize(
        object.host,
        specifiedType: const FullType(String),
      );
    }
    if (object.port != null) {
      yield r'port';
      yield serializers.serialize(
        object.port,
        specifiedType: const FullType(int),
      );
    }
    if (object.username != null) {
      yield r'username';
      yield serializers.serialize(
        object.username,
        specifiedType: const FullType(String),
      );
    }
    if (object.password != null) {
      yield r'password';
      yield serializers.serialize(
        object.password,
        specifiedType: const FullType(String),
      );
    }
    if (object.topicPrefix != null) {
      yield r'topic_prefix';
      yield serializers.serialize(
        object.topicPrefix,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DutyStateMqtt object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DutyStateMqttBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'host':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.host = valueDes;
          break;
        case r'port':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.port = valueDes;
          break;
        case r'username':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.username = valueDes;
          break;
        case r'password':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.password = valueDes;
          break;
        case r'topic_prefix':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.topicPrefix = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DutyStateMqtt deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DutyStateMqttBuilder();
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

