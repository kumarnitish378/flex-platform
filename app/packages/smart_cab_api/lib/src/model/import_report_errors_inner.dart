//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'import_report_errors_inner.g.dart';

/// ImportReportErrorsInner
///
/// Properties:
/// * [row] 
/// * [field] 
/// * [message] 
@BuiltValue()
abstract class ImportReportErrorsInner implements Built<ImportReportErrorsInner, ImportReportErrorsInnerBuilder> {
  @BuiltValueField(wireName: r'row')
  int? get row;

  @BuiltValueField(wireName: r'field')
  String? get field;

  @BuiltValueField(wireName: r'message')
  String? get message;

  ImportReportErrorsInner._();

  factory ImportReportErrorsInner([void updates(ImportReportErrorsInnerBuilder b)]) = _$ImportReportErrorsInner;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ImportReportErrorsInnerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ImportReportErrorsInner> get serializer => _$ImportReportErrorsInnerSerializer();
}

class _$ImportReportErrorsInnerSerializer implements PrimitiveSerializer<ImportReportErrorsInner> {
  @override
  final Iterable<Type> types = const [ImportReportErrorsInner, _$ImportReportErrorsInner];

  @override
  final String wireName = r'ImportReportErrorsInner';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ImportReportErrorsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.row != null) {
      yield r'row';
      yield serializers.serialize(
        object.row,
        specifiedType: const FullType(int),
      );
    }
    if (object.field != null) {
      yield r'field';
      yield serializers.serialize(
        object.field,
        specifiedType: const FullType(String),
      );
    }
    if (object.message != null) {
      yield r'message';
      yield serializers.serialize(
        object.message,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ImportReportErrorsInner object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ImportReportErrorsInnerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'row':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.row = valueDes;
          break;
        case r'field':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.field = valueDes;
          break;
        case r'message':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.message = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ImportReportErrorsInner deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ImportReportErrorsInnerBuilder();
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

