//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/billing_export_summary.dart';
import 'package:smart_cab_api/src/model/billing_export_treatment.dart';
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/billing_export_rows_inner.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'billing_export.g.dart';

/// BillingExport
///
/// Properties:
/// * [clientId] 
/// * [clientName] 
/// * [month] 
/// * [treatment] 
/// * [summary] 
/// * [rows] 
@BuiltValue()
abstract class BillingExport implements Built<BillingExport, BillingExportBuilder> {
  @BuiltValueField(wireName: r'client_id')
  String get clientId;

  @BuiltValueField(wireName: r'client_name')
  String get clientName;

  @BuiltValueField(wireName: r'month')
  String get month;

  @BuiltValueField(wireName: r'treatment')
  BillingExportTreatment get treatment;

  @BuiltValueField(wireName: r'summary')
  BillingExportSummary get summary;

  @BuiltValueField(wireName: r'rows')
  BuiltList<BillingExportRowsInner> get rows;

  BillingExport._();

  factory BillingExport([void updates(BillingExportBuilder b)]) = _$BillingExport;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(BillingExportBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<BillingExport> get serializer => _$BillingExportSerializer();
}

class _$BillingExportSerializer implements PrimitiveSerializer<BillingExport> {
  @override
  final Iterable<Type> types = const [BillingExport, _$BillingExport];

  @override
  final String wireName = r'BillingExport';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    BillingExport object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'client_id';
    yield serializers.serialize(
      object.clientId,
      specifiedType: const FullType(String),
    );
    yield r'client_name';
    yield serializers.serialize(
      object.clientName,
      specifiedType: const FullType(String),
    );
    yield r'month';
    yield serializers.serialize(
      object.month,
      specifiedType: const FullType(String),
    );
    yield r'treatment';
    yield serializers.serialize(
      object.treatment,
      specifiedType: const FullType(BillingExportTreatment),
    );
    yield r'summary';
    yield serializers.serialize(
      object.summary,
      specifiedType: const FullType(BillingExportSummary),
    );
    yield r'rows';
    yield serializers.serialize(
      object.rows,
      specifiedType: const FullType(BuiltList, [FullType(BillingExportRowsInner)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    BillingExport object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required BillingExportBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.clientId = valueDes;
          break;
        case r'client_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.clientName = valueDes;
          break;
        case r'month':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.month = valueDes;
          break;
        case r'treatment':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BillingExportTreatment),
          ) as BillingExportTreatment;
          result.treatment.replace(valueDes);
          break;
        case r'summary':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BillingExportSummary),
          ) as BillingExportSummary;
          result.summary.replace(valueDes);
          break;
        case r'rows':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(BillingExportRowsInner)]),
          ) as BuiltList<BillingExportRowsInner>;
          result.rows.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  BillingExport deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = BillingExportBuilder();
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

