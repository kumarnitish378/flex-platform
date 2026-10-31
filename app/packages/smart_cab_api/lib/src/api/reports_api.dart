//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

import 'dart:async';

import 'package:built_value/json_object.dart';
import 'package:built_value/serializer.dart';
import 'package:dio/dio.dart';

import 'package:smart_cab_api/src/api_util.dart';
import 'package:smart_cab_api/src/model/billing_export.dart';
import 'package:smart_cab_api/src/model/date.dart';
import 'package:smart_cab_api/src/model/operations_report.dart';
import 'package:smart_cab_api/src/model/trip_report.dart';

class ReportsApi {

  final Dio _dio;

  final Serializers _serializers;

  const ReportsApi(this._dio, this._serializers);

  /// One client&#39;s month as quantities - rides, trips, riders, kilometres (B38, OPA-06)
  /// Requires &#x60;billing.view&#x60; (operator admin, client admin). A client admin is invoiced for their own people whatever &#x60;client_id&#x60; they send; an operator admin must name one.  **Quantities, not money.** What the operator bills on is OQ-03 (pricing) and OQ-01 (the pilot operator), both open, so this stops short of a price and states the three treatments an invoice would otherwise guess at, in &#x60;treatment&#x60;: &#x60;no_show_billable&#x60; (default true), &#x60;late_cancel_billable&#x60; (default false; a request cancelled while still queued is never billable) and &#x60;distance_basis&#x60; (&#x60;trip_share&#x60; - an equal share of the kilometres the cab actually drove, so a trip&#39;s shares add up to its measured distance - or &#x60;direct&#x60;). **All three defaults are provisional.**  A month is the operator&#39;s calendar month in their own timezone, by when the rider asked. One row per ride, whether or not it is billable, with &#x60;billable_reason&#x60; saying why - so an invoice can be audited line by line against the &#x60;ride_request&#x60; and &#x60;trip&#x60; rows it came from. 
  ///
  /// Parameters:
  /// * [month] - YYYY-MM
  /// * [clientId] 
  /// * [format] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [BillingExport] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<BillingExport>> reportsBillingGet({ 
    required String month,
    String? clientId,
    String? format = 'json',
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/reports/billing';
    final _options = Options(
      method: r'GET',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      validateStatus: validateStatus,
    );

    final _queryParameters = <String, dynamic>{
      r'month': encodeQueryParameter(_serializers, month, const FullType(String)),
      if (clientId != null) r'client_id': encodeQueryParameter(_serializers, clientId, const FullType(String)),
      if (format != null) r'format': encodeQueryParameter(_serializers, format, const FullType(String)),
    };

    final _response = await _dio.request<Object>(
      _path,
      options: _options,
      queryParameters: _queryParameters,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    BillingExport? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(BillingExport),
      ) as BillingExport;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<BillingExport>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

  /// The full operator report (B39, OPA-05)
  /// Waits, pooling, cab-km, overrides and suggestion acceptance for a period, computed from the records the platform keeps. Requires &#x60;report.operational.view&#x60; (operator admin, supervisor); a client admin has no operational report.  **Days are the operator&#39;s calendar days** in their own timezone, both ends inclusive.  **Cab-km and vehicles used come from what the cabs drove**: &#x60;trip.actual_distance_m&#x60;, measured from the cab&#39;s pings when the driver completes the trip - never from what dispatch planned. A trip with no pings has no distance, and is left out of the average rather than counted as zero kilometres.  **&#x60;suggestions.acceptance_rate&#x60; is OQ-39 stated, not decided.** It counts only the system&#39;s first choice that a person or the failsafe settled in the period; a &#x60;failsafe_assigned&#x60; offer is never an acceptance (nobody agreed to it) and a &#x60;superseded&#x60; one is never a verdict. Two readings are returned because the open question names two: &#x60;acceptance_rate&#x60; (approved) and &#x60;acceptance_rate_with_alternatives&#x60; (approved, or rejected in favour of a cab the system had also offered). Say which one when quoting either. 
  ///
  /// Parameters:
  /// * [from] 
  /// * [to] 
  /// * [clientId] 
  /// * [format] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [OperationsReport] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<OperationsReport>> reportsOperationsGet({ 
    required Date from,
    required Date to,
    String? clientId,
    String? format = 'json',
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/reports/operations';
    final _options = Options(
      method: r'GET',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      validateStatus: validateStatus,
    );

    final _queryParameters = <String, dynamic>{
      r'from': encodeQueryParameter(_serializers, from, const FullType(Date)),
      r'to': encodeQueryParameter(_serializers, to, const FullType(Date)),
      if (clientId != null) r'client_id': encodeQueryParameter(_serializers, clientId, const FullType(String)),
      if (format != null) r'format': encodeQueryParameter(_serializers, format, const FullType(String)),
    };

    final _response = await _dio.request<Object>(
      _path,
      options: _options,
      queryParameters: _queryParameters,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    OperationsReport? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(OperationsReport),
      ) as OperationsReport;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<OperationsReport>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

  /// reportsTripsGet
  /// 
  ///
  /// Parameters:
  /// * [from] 
  /// * [to] 
  /// * [clientId] 
  /// * [format] 
  /// * [cancelToken] - A [CancelToken] that can be used to cancel the operation
  /// * [headers] - Can be used to add additional headers to the request
  /// * [extras] - Can be used to add flags to the request
  /// * [validateStatus] - A [ValidateStatus] callback that can be used to determine request success based on the HTTP status of the response
  /// * [onSendProgress] - A [ProgressCallback] that can be used to get the send progress
  /// * [onReceiveProgress] - A [ProgressCallback] that can be used to get the receive progress
  ///
  /// Returns a [Future] containing a [Response] with a [TripReport] as data
  /// Throws [DioException] if API call or serialization fails
  Future<Response<TripReport>> reportsTripsGet({ 
    required Date from,
    required Date to,
    String? clientId,
    String? format = 'json',
    CancelToken? cancelToken,
    Map<String, dynamic>? headers,
    Map<String, dynamic>? extra,
    ValidateStatus? validateStatus,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) async {
    final _path = r'/reports/trips';
    final _options = Options(
      method: r'GET',
      headers: <String, dynamic>{
        ...?headers,
      },
      extra: <String, dynamic>{
        'secure': <Map<String, String>>[
          {
            'type': 'http',
            'scheme': 'bearer',
            'name': 'bearerAuth',
          },
        ],
        ...?extra,
      },
      validateStatus: validateStatus,
    );

    final _queryParameters = <String, dynamic>{
      r'from': encodeQueryParameter(_serializers, from, const FullType(Date)),
      r'to': encodeQueryParameter(_serializers, to, const FullType(Date)),
      if (clientId != null) r'client_id': encodeQueryParameter(_serializers, clientId, const FullType(String)),
      if (format != null) r'format': encodeQueryParameter(_serializers, format, const FullType(String)),
    };

    final _response = await _dio.request<Object>(
      _path,
      options: _options,
      queryParameters: _queryParameters,
      cancelToken: cancelToken,
      onSendProgress: onSendProgress,
      onReceiveProgress: onReceiveProgress,
    );

    TripReport? _responseData;

    try {
      final rawResponse = _response.data;
      _responseData = rawResponse == null ? null : _serializers.deserialize(
        rawResponse,
        specifiedType: const FullType(TripReport),
      ) as TripReport;

    } catch (error, stackTrace) {
      throw DioException(
        requestOptions: _response.requestOptions,
        response: _response,
        type: DioExceptionType.unknown,
        error: error,
        stackTrace: stackTrace,
      );
    }

    return Response<TripReport>(
      data: _responseData,
      headers: _response.headers,
      isRedirect: _response.isRedirect,
      requestOptions: _response.requestOptions,
      redirects: _response.redirects,
      statusCode: _response.statusCode,
      statusMessage: _response.statusMessage,
      extra: _response.extra,
    );
  }

}
