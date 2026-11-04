import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/router.dart';
import 'package:smart_cab/core/session.dart';

/// Role-based routing (A01, coding-standards.md section 3 rule 2).
///
/// Hiding a screen is not security - the server authorises every call (hard rule 3) -
/// but offering a driver a screen whose every button returns 403 is a bug of its own,
/// so what each role may open is worth asserting directly.
void main() {
  group('every role has somewhere to land', () {
    test('no role falls through to a missing home', () {
      for (final Role role in Role.values) {
        expect(
          homeForRole[role],
          isNotNull,
          reason: '$role has no home route, so login would strand them',
        );
      }
    });

    test('platform_admin shares the operator admin screens', () {
      // It holds every permission (`roles-and-permissions.md`), so giving it a separate
      // set of screens would mean maintaining two of everything.
      expect(homeForRole[Role.platformAdmin], homeForRole[Role.operatorAdmin]);
    });
  });

  group('a role may only open its own screens', () {
    test('an employee cannot open the dispatch board', () {
      expect(roleMayOpen(Role.employee, '/supervisor'), isFalse);
      expect(roleMayOpen(Role.employee, '/admin'), isFalse);
      expect(roleMayOpen(Role.employee, '/employee'), isTrue);
    });

    test('a driver cannot open the admin screens', () {
      expect(roleMayOpen(Role.driver, '/admin'), isFalse);
      expect(roleMayOpen(Role.driver, '/driver'), isTrue);
    });

    test('a client admin sees only their own client', () {
      expect(roleMayOpen(Role.clientAdmin, '/client'), isTrue);
      expect(roleMayOpen(Role.clientAdmin, '/admin'), isFalse);
      // The dispatch board is the whole operator's work, and a client admin is scoped
      // to one client - the same reason B13 refused them the operator WebSocket feed.
      expect(roleMayOpen(Role.clientAdmin, '/supervisor'), isFalse);
    });

    test('a supervisor may open the board, and an operator admin may too', () {
      expect(roleMayOpen(Role.supervisor, '/supervisor'), isTrue);
      expect(roleMayOpen(Role.operatorAdmin, '/supervisor'), isTrue);
    });

    test('nested routes inherit their prefix', () {
      expect(roleMayOpen(Role.driver, '/driver/trips/abc'), isTrue);
      expect(roleMayOpen(Role.driver, '/admin/vehicles/abc'), isFalse);
    });

    test('a prefix match must be a path segment, not a string prefix', () {
      // `/driverish` is not under `/driver`, and a naive `startsWith` would say it was.
      expect(roleMayOpen(Role.employee, '/driverish'), isTrue);
    });

    test('signed out opens nothing', () {
      expect(roleMayOpen(null, '/employee'), isFalse);
    });
  });

  group('session', () {
    test('wire names match the backend exactly', () {
      // These strings go on the wire in `X-Active-Role`; camelCase would 422.
      expect(Role.operatorAdmin.wireName, 'operator_admin');
      expect(Role.clientAdmin.wireName, 'client_admin');
      expect(Role.fromWire('platform_admin'), Role.platformAdmin);
      expect(Role.fromWire('nonsense'), isNull);
      expect(Role.fromWire(null), isNull);
    });

    test('nobody is signed in by default', () {
      expect(Session.none.isSignedIn, isFalse);
      expect(Session.none.canSwitchRole, isFalse);
    });

    test('a session needs both a token and an active role', () {
      const Session halfway = Session(roles: <Role>[Role.driver], accessToken: 'x');
      expect(halfway.isSignedIn, isFalse, reason: 'no active role yet');
    });

    test('the switcher appears only for someone holding two roles', () {
      const Session one = Session(roles: <Role>[Role.employee]);
      const Session two = Session(roles: <Role>[Role.employee, Role.supervisor]);
      expect(one.canSwitchRole, isFalse);
      expect(two.canSwitchRole, isTrue);
    });
  });
}
