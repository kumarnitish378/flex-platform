// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_requests_request_id_candidates_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchRequestsRequestIdCandidatesGet200Response
    extends DispatchRequestsRequestIdCandidatesGet200Response {
  @override
  final BuiltList<Candidate> items;

  factory _$DispatchRequestsRequestIdCandidatesGet200Response(
          [void Function(
                  DispatchRequestsRequestIdCandidatesGet200ResponseBuilder)?
              updates]) =>
      (DispatchRequestsRequestIdCandidatesGet200ResponseBuilder()
            ..update(updates))
          ._build();

  _$DispatchRequestsRequestIdCandidatesGet200Response._({required this.items})
      : super._();
  @override
  DispatchRequestsRequestIdCandidatesGet200Response rebuild(
          void Function(
                  DispatchRequestsRequestIdCandidatesGet200ResponseBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchRequestsRequestIdCandidatesGet200ResponseBuilder toBuilder() =>
      DispatchRequestsRequestIdCandidatesGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchRequestsRequestIdCandidatesGet200Response &&
        items == other.items;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, items.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(
            r'DispatchRequestsRequestIdCandidatesGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DispatchRequestsRequestIdCandidatesGet200ResponseBuilder
    implements
        Builder<DispatchRequestsRequestIdCandidatesGet200Response,
            DispatchRequestsRequestIdCandidatesGet200ResponseBuilder> {
  _$DispatchRequestsRequestIdCandidatesGet200Response? _$v;

  ListBuilder<Candidate>? _items;
  ListBuilder<Candidate> get items =>
      _$this._items ??= ListBuilder<Candidate>();
  set items(ListBuilder<Candidate>? items) => _$this._items = items;

  DispatchRequestsRequestIdCandidatesGet200ResponseBuilder() {
    DispatchRequestsRequestIdCandidatesGet200Response._defaults(this);
  }

  DispatchRequestsRequestIdCandidatesGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchRequestsRequestIdCandidatesGet200Response other) {
    _$v = other as _$DispatchRequestsRequestIdCandidatesGet200Response;
  }

  @override
  void update(
      void Function(DispatchRequestsRequestIdCandidatesGet200ResponseBuilder)?
          updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchRequestsRequestIdCandidatesGet200Response build() => _build();

  _$DispatchRequestsRequestIdCandidatesGet200Response _build() {
    _$DispatchRequestsRequestIdCandidatesGet200Response _$result;
    try {
      _$result = _$v ??
          _$DispatchRequestsRequestIdCandidatesGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DispatchRequestsRequestIdCandidatesGet200Response',
            _$failedField,
            e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
