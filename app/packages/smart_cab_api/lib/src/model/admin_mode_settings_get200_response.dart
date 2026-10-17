//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/mode_setting.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_mode_settings_get200_response.g.dart';

/// AdminModeSettingsGet200Response
///
/// Properties:
/// * [items] 
/// * [overlapping] - pairs of setting ids at equal specificity that could both match
@BuiltValue()
abstract class AdminModeSettingsGet200Response implements Built<AdminModeSettingsGet200Response, AdminModeSettingsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<ModeSetting>? get items;

  /// pairs of setting ids at equal specificity that could both match
  @BuiltValueField(wireName: r'overlapping')
  BuiltList<BuiltList<String>>? get overlapping;

  AdminModeSettingsGet200Response._();

  factory AdminModeSettingsGet200Response([void updates(AdminModeSettingsGet200ResponseBuilder b)]) = _$AdminModeSettingsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminModeSettingsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminModeSettingsGet200Response> get serializer => _$AdminModeSettingsGet200ResponseSerializer();
}

class _$AdminModeSettingsGet200ResponseSerializer implements PrimitiveSerializer<AdminModeSettingsGet200Response> {
  @override
  final Iterable<Type> types = const [AdminModeSettingsGet200Response, _$AdminModeSettingsGet200Response];

  @override
  final String wireName = r'AdminModeSettingsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminModeSettingsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(ModeSetting)]),
      );
    }
    if (object.overlapping != null) {
      yield r'overlapping';
      yield serializers.serialize(
        object.overlapping,
        specifiedType: const FullType(BuiltList, [FullType(BuiltList, [FullType(String)])]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminModeSettingsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminModeSettingsGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(ModeSetting)]),
          ) as BuiltList<ModeSetting>;
          result.items.replace(valueDes);
          break;
        case r'overlapping':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(BuiltList, [FullType(String)])]),
          ) as BuiltList<BuiltList<String>>;
          result.overlapping.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  AdminModeSettingsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminModeSettingsGet200ResponseBuilder();
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

