//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/import_report_errors_inner.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'import_report.g.dart';

/// ImportReport
///
/// Properties:
/// * [totalRows] 
/// * [validRows] 
/// * [created] 
/// * [updated] 
/// * [errors] 
@BuiltValue()
abstract class ImportReport implements Built<ImportReport, ImportReportBuilder> {
  @BuiltValueField(wireName: r'total_rows')
  int? get totalRows;

  @BuiltValueField(wireName: r'valid_rows')
  int? get validRows;

  @BuiltValueField(wireName: r'created')
  int? get created;

  @BuiltValueField(wireName: r'updated')
  int? get updated;

  @BuiltValueField(wireName: r'errors')
  BuiltList<ImportReportErrorsInner>? get errors;

  ImportReport._();

  factory ImportReport([void updates(ImportReportBuilder b)]) = _$ImportReport;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ImportReportBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ImportReport> get serializer => _$ImportReportSerializer();
}

class _$ImportReportSerializer implements PrimitiveSerializer<ImportReport> {
  @override
  final Iterable<Type> types = const [ImportReport, _$ImportReport];

  @override
  final String wireName = r'ImportReport';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ImportReport object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.totalRows != null) {
      yield r'total_rows';
      yield serializers.serialize(
        object.totalRows,
        specifiedType: const FullType(int),
      );
    }
    if (object.validRows != null) {
      yield r'valid_rows';
      yield serializers.serialize(
        object.validRows,
        specifiedType: const FullType(int),
      );
    }
    if (object.created != null) {
      yield r'created';
      yield serializers.serialize(
        object.created,
        specifiedType: const FullType(int),
      );
    }
    if (object.updated != null) {
      yield r'updated';
      yield serializers.serialize(
        object.updated,
        specifiedType: const FullType(int),
      );
    }
    if (object.errors != null) {
      yield r'errors';
      yield serializers.serialize(
        object.errors,
        specifiedType: const FullType(BuiltList, [FullType(ImportReportErrorsInner)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ImportReport object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ImportReportBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'total_rows':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.totalRows = valueDes;
          break;
        case r'valid_rows':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.validRows = valueDes;
          break;
        case r'created':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.created = valueDes;
          break;
        case r'updated':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.updated = valueDes;
          break;
        case r'errors':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(ImportReportErrorsInner)]),
          ) as BuiltList<ImportReportErrorsInner>;
          result.errors.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ImportReport deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ImportReportBuilder();
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

