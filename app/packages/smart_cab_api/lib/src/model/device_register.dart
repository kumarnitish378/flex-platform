//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'device_register.g.dart';

/// DeviceRegister
///
/// Properties:
/// * [platform] 
/// * [pushToken] 
/// * [appVersion] 
@BuiltValue()
abstract class DeviceRegister implements Built<DeviceRegister, DeviceRegisterBuilder> {
  @BuiltValueField(wireName: r'platform')
  DeviceRegisterPlatformEnum get platform;
  // enum platformEnum {  android,  ios,  web,  };

  @BuiltValueField(wireName: r'push_token')
  String get pushToken;

  @BuiltValueField(wireName: r'app_version')
  String get appVersion;

  DeviceRegister._();

  factory DeviceRegister([void updates(DeviceRegisterBuilder b)]) = _$DeviceRegister;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DeviceRegisterBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DeviceRegister> get serializer => _$DeviceRegisterSerializer();
}

class _$DeviceRegisterSerializer implements PrimitiveSerializer<DeviceRegister> {
  @override
  final Iterable<Type> types = const [DeviceRegister, _$DeviceRegister];

  @override
  final String wireName = r'DeviceRegister';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DeviceRegister object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'platform';
    yield serializers.serialize(
      object.platform,
      specifiedType: const FullType(DeviceRegisterPlatformEnum),
    );
    yield r'push_token';
    yield serializers.serialize(
      object.pushToken,
      specifiedType: const FullType(String),
    );
    yield r'app_version';
    yield serializers.serialize(
      object.appVersion,
      specifiedType: const FullType(String),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DeviceRegister object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DeviceRegisterBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'platform':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DeviceRegisterPlatformEnum),
          ) as DeviceRegisterPlatformEnum;
          result.platform = valueDes;
          break;
        case r'push_token':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.pushToken = valueDes;
          break;
        case r'app_version':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.appVersion = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DeviceRegister deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DeviceRegisterBuilder();
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

class DeviceRegisterPlatformEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'android')
  static const DeviceRegisterPlatformEnum android = _$deviceRegisterPlatformEnum_android;
  @BuiltValueEnumConst(wireName: r'ios')
  static const DeviceRegisterPlatformEnum ios = _$deviceRegisterPlatformEnum_ios;
  @BuiltValueEnumConst(wireName: r'web')
  static const DeviceRegisterPlatformEnum web = _$deviceRegisterPlatformEnum_web;

  static Serializer<DeviceRegisterPlatformEnum> get serializer => _$deviceRegisterPlatformEnumSerializer;

  const DeviceRegisterPlatformEnum._(String name): super(name);

  static BuiltSet<DeviceRegisterPlatformEnum> get values => _$deviceRegisterPlatformEnumValues;
  static DeviceRegisterPlatformEnum valueOf(String name) => _$deviceRegisterPlatformEnumValueOf(name);
}

