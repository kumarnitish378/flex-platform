import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/screens.dart';
import 'package:smart_cab/core/session.dart';

/// Invariants of the screen catalogue (A04).
///
/// These are the mistakes the table exists to prevent, asserted directly. Each one is
/// a defect that a human would only find by signing in as that role and tapping: a tab
/// that bounces straight back home, two screens claiming one path, a destination whose
/// path wants a trip id that a tab bar has no way to supply.
void main() {
  group('the catalogue is self-consistent', () {
    test('every screen id and path is unique', () {
      final Set<String> ids = AppScreen.values.map((AppScreen s) => s.id).toSet();
      final Set<String> paths = AppScreen.values.map((AppScreen s) => s.path).toSet();
      expect(ids.length, AppScreen.values.length, reason: 'duplicate screen id');
      expect(paths.length, AppScreen.values.length, reason: 'two screens share a path');
    });

    test('a screen sits under its own section prefix', () {
      // This is what makes the role gate safe: it reads the prefix, so a screen filed
      // under the wrong section would be opened by the wrong role.
      for (final AppScreen screen in AppScreen.values) {
        if (screen.section == AppSection.common) {
          continue;
        }
        expect(
          screen.path == screen.section.prefix ||
              screen.path.startsWith('${screen.section.prefix}/'),
          isTrue,
          reason: '${screen.id} is in ${screen.section.name} but its path is '
              '${screen.path}, so the role gate would not cover it',
        );
      }
    });

    test('common screens are top-level, so every role keeps them', () {
      for (final AppScreen screen in AppScreen.values) {
        if (screen.section != AppSection.common) {
          continue;
        }
        expect(
          rolesForRoute.keys.any(
            (String prefix) =>
                screen.path == prefix || screen.path.startsWith('$prefix/'),
          ),
          isFalse,
          reason: '${screen.id} is common but sits under a role prefix, which would '
              'hide it from every other role',
        );
      }
    });
  });

  group('every role can reach everything it is offered', () {
    test('no destination is a tab that bounces back home', () {
      for (final Role role in Role.values) {
        for (final AppScreen screen in destinationsFor(role)) {
          expect(
            screen.section.roles.contains(role) ||
                screen.section == AppSection.common,
            isTrue,
            reason: '$role is offered ${screen.id} but may not open it, so tapping '
                'that tab would redirect home',
          );
        }
      }
    });

    test('no destination needs a path parameter', () {
      for (final Role role in Role.values) {
        for (final AppScreen screen in destinationsFor(role)) {
          expect(
            screen.isParameterised,
            isFalse,
            reason: '${screen.id} is a destination but its path ${screen.path} wants '
                'a value a navigation bar has no way to supply',
          );
        }
      }
    });

    test('every role has at least one tab and at most four', () {
      // Four plus "More" is five, which is Material's limit for a navigation bar.
      for (final Role role in Role.values) {
        final List<AppScreen>? primary = primaryDestinations[role];
        expect(primary, isNotNull, reason: '$role has no destinations');
        expect(primary, isNotEmpty, reason: '$role has an empty navigation bar');
        expect(
          primary!.length,
          lessThanOrEqualTo(4),
          reason: '$role has ${primary.length} tabs; the fifth slot is "More"',
        );
      }
    });

    test('a role is never offered the same screen twice', () {
      for (final Role role in Role.values) {
        final List<AppScreen> all = destinationsFor(role);
        expect(
          all.toSet().length,
          all.length,
          reason: '$role is offered a screen in both a tab and "More"',
        );
      }
    });

    test('notifications and the profile belong to everybody', () {
      for (final Role role in Role.values) {
        expect(destinationsFor(role), contains(AppScreen.notifications));
        expect(destinationsFor(role), contains(AppScreen.profile));
      }
    });
  });

  group('home', () {
    test('home is the first tab, for every role', () {
      for (final Role role in Role.values) {
        expect(homeForRole[role], primaryDestinations[role]!.first.path);
      }
    });

    test('every section with screens has a gate', () {
      for (final AppSection section in AppSection.values) {
        if (section.prefix.isEmpty) {
          continue;
        }
        expect(rolesForRoute[section.prefix], isNotEmpty);
      }
    });
  });
}
