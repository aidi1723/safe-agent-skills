# Repository Exploration Evidence Map

Use this map to gather only the context required for the current task.

## Authority And Entry Points

Record repository and directory-level instructions, package manifests, build
and test configuration, runtime launchers, routes, commands, job definitions,
and release scripts. Note which instruction applies to each target path.

## Ownership And Flow

Trace the requested behavior from an observable entry point through the
responsible modules, shared contracts, state or storage boundaries, and
downstream consumers. Support relationships with imports, registrations,
configuration, schemas, tests, or call sites rather than directory names.

## Exclusions

Identify generated files, vendored code, dependency caches, build artifacts,
snapshots, fixtures, migrations, and external submodules. State whether they
are inputs, outputs, review evidence, or prohibited edit targets.

## Change Map

List the smallest likely edit surface, tests that exercise it, compatibility
risks, commands needed for verification, and unknowns that could expand scope.
Stop exploring when these fields are supported well enough to plan safely.
