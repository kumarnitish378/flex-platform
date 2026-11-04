//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'escort_confirmation.g.dart';

/// EscortConfirmation
///
/// Properties:
/// * [basis] 
/// * [note] 
@BuiltValue()
abstract class EscortConfirmation implements Built<EscortConfirmation, EscortConfirmationBuilder> {
  @BuiltValueField(wireName: r'basis')
  EscortConfirmationBasisEnum get basis;
  // enum basisEnum {  escort_arranged,  male_co_rider_present,  };

  @BuiltValueField(wireName: r'note')
  String? get note;

  EscortConfirmation._();

  factory EscortConfirmation([void updates(EscortConfirmationBuilder b)]) = _$EscortConfirmation;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(EscortConfirmationBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<EscortConfirmation> get serializer => _$EscortConfirmationSerializer();
}

class _$EscortConfirmationSerializer implements PrimitiveSerializer<EscortConfirmation> {
  @override
  final Iterable<Type> types = const [EscortConfirmation, _$EscortConfirmation];

  @override
  final String wireName = r'EscortConfirmation';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    EscortConfirmation object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'basis';
    yield serializers.serialize(
      object.basis,
      specifiedType: const FullType(EscortConfirmationBasisEnum),
    );
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    EscortConfirmation object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required EscortConfirmationBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'basis':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(EscortConfirmationBasisEnum),
          ) as EscortConfirmationBasisEnum;
          result.basis = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.note = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  EscortConfirmation deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = EscortConfirmationBuilder();
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

class EscortConfirmationBasisEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'escort_arranged')
  static const EscortConfirmationBasisEnum escortArranged = _$escortConfirmationBasisEnum_escortArranged;
  @BuiltValueEnumConst(wireName: r'male_co_rider_present')
  static const EscortConfirmationBasisEnum maleCoRiderPresent = _$escortConfirmationBasisEnum_maleCoRiderPresent;

  static Serializer<EscortConfirmationBasisEnum> get serializer => _$escortConfirmationBasisEnumSerializer;

  const EscortConfirmationBasisEnum._(String name): super(name);

  static BuiltSet<EscortConfirmationBasisEnum> get values => _$escortConfirmationBasisEnumValues;
  static EscortConfirmationBasisEnum valueOf(String name) => _$escortConfirmationBasisEnumValueOf(name);
}

