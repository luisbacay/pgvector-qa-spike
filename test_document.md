> Synthetic test document. Project Halcyon, its dates, team and figures are invented for testing. Nothing here describes a real project.

# Internal Product Brief: Project Halcyon

Project Halcyon is an internal MulTech initiative started in March 2025 to
build a shared component library across all Nuvaris products. It is led
by a three-person working group and reports directly to the CTO.

## Purpose

Before Halcyon, Admiva, Admita, Arciva, and Talenta each implemented their
own UI components independently, causing visual inconsistency across the
Nuvaris product line and duplicated engineering effort. Halcyon centralizes
button styles, form inputs, navigation patterns, and the color token system
used across all four products.

## Technical Details

Halcyon is built on top of shadcn/ui and Tailwind CSS. It is distributed
internally as a private npm package named @nuvaris/halcyon-ui. The package
is versioned using semantic versioning, and as of the most recent internal
release, it is on version 2.3.1.

The design token file at the core of Halcyon defines exactly 14 named
colors, 6 spacing units, and 3 border radius values. The primary brand
color token is named "nuvaris-teal" and has the hex value #0F7A6E.

## Adoption Status

As of the writing of this brief, Talenta has fully adopted Halcyon across
its entire frontend. Admiva has adopted Halcyon for 60% of its screens,
with the remaining 40% scheduled for migration in the next development
cycle. Admita and Arciva have not yet begun migration, as both are
built on vanilla JavaScript SPAs rather than a component framework,
which makes Halcyon adoption a larger undertaking requiring an
architecture change first.

## Known Issues

There is one open bug in Halcyon version 2.3.1: the DatePicker component
renders incorrectly on Safari when the browser's system time zone is set
to a UTC offset with a half-hour increment, such as India Standard Time
(UTC+5:30) or Newfoundland Standard Time (UTC-3:30). This bug is tracked
internally as HALCYON-114 and has not yet been fixed.

## Governance

Any new component added to Halcyon must be reviewed and approved by at
least two members of the three-person working group before merging into
the main branch. This rule was established in June 2025 after an
unreviewed component caused a visual regression across three products
simultaneously.
