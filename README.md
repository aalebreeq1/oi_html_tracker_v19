# OI HTML Tracking

Track changes to selected HTML fields using Odoo’s native chatter.

| Property | Value |
|---|---|
| Technical name | `oi_html_track` |
| Version | `19.0.0.0.0` |
| Target | Odoo 19 |
| Dependencies | `base`, `mail` |

## Usage

Enable tracking through the field attribute:

```python
description = fields.Html(html_track=True)
```

The field must be stored, and its model must inherit `mail.thread`.

Normal HTML fields are stored by default. Computed or related fields may require `store=True`.

Example integration:

```python
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    description = fields.Html(html_track=True)
```

The integration addon must depend on the owning application and this addon:

```python
"depends": ["project", "oi_html_track"],
```

No application-specific `_mail_track()` override is required.

## Behavior

The addon automatically:

- Registers `html_track` as an HTML field parameter.
- Includes marked, stored fields in native tracking.
- Stores complete previous and saved HTML snapshots.
- Extracts added and removed text.
- Generates standard messages using field labels.
- Displays previous text alongside changed fragments.

| Saved change | Tracking display |
|---|---|
| `Hello` → `Hello world` | `Hello → Added: world` |
| `Hello world` → `Hello` | `Hello world → Removed: world` |
| `Task` → `Tasks` | `Task → Added: s` |
| `cat` → `car` | `cat → Added: r \| Removed: t` |

Messages distinguish additions, removals, combined changes, and generic HTML updates. Author and timestamp information comes from native chatter.

## Architecture

```text
models/
├── mail_thread.py
└── mail_tracking_value.py
```

### `mail_thread.py`

| Method | Responsibility |
|---|---|
| `_valid_field_parameter()` | Accepts `html_track` on HTML fields. |
| `_track_get_fields()` | Adds accessible, stored, marked HTML fields to native tracking. |
| `_mail_track()` | Classifies changes, selects messages, and supplies the combined tracking body. |

Field discovery is cached by user and superuser mode.

The tracking hook preserves existing pending/default messages at its execution point. `Markup("<br/>").join(messages)` separates messages and escapes ordinary dynamic text.

### `mail_tracking_value.py`

| Method | Responsibility |
|---|---|
| `_create_tracking_values()` | Routes marked HTML snapshots into native Text tracking columns. |
| `_get_html_tracking_diff()` | Extracts changed fragments from normalized text. |
| `_format_display_value()` | Displays previous text and added/removed fragments. |

The actual business field remains HTML. Complete snapshots are stored in:

```text
mail.tracking.value.old_value_text
mail.tracking.value.new_value_text
```

The copied tracking metadata uses `type="text"` solely to reuse native storage.

## Change Detection

Detection has two stages:

1. Native Odoo tracking compares the previous and saved HTML values.
2. The addon compares their normalized text for display.

Text normalization uses:

```python
html_to_inner_content(value or "")
```

Character comparison uses:

```python
SequenceMatcher(
    None, old_text, new_text, autojunk=False
)
```

Each operation contains:

```python
(action, old_start, old_end, new_start, new_end)
```

| Operation | Old fragment | New fragment |
|---|---|---|
| `equal` | Unchanged | Unchanged; operation skipped |
| `insert` | Empty | Added text |
| `delete` | Removed text | Empty |
| `replace` | Removed text | Added text |

The helper trims fragments, discards empty fragments, and joins separate regions with `…`.

A replacement produces both added and removed text. Separate additions and deletions in one save produce the same combined message category.

HTML changes without extracted text fragments use a generic update message.

## Transactions and Access

- Tracking follows Odoo’s ORM and transaction lifecycle.
- Repeated writes generally compare the first captured value with the final value.
- Rollback prevents a committed tracking entry.
- Initial creation and copying follow native creation behavior.
- Native record and field-access filtering remains in use.
- Fields configured with `groups` retain native tracking values, but their automatic shared body messages are skipped.
- Notification behavior follows existing Odoo subtypes and application logic.

## Strengths

- Declarative, reusable field configuration.
- Automatic messages without per-model tracking overrides.
- Complete HTML snapshots with focused change display.
- Multiple marked fields supported in one update.
- Native tracking storage and transaction handling.
- Server-side implementation without custom JavaScript.
- Translation-ready message strings.

## Limitations

- Comparison is character-based and does not understand sentence meaning.
- Formatting, images, link targets, and whitespace changes may receive generic messages.
- Displayed fragments are not a reversible patch or keystroke history.
- The complete previous text remains visible, which can produce long entries.
- Full snapshots increase storage, especially with inline image data.
- Long or repetitive text can make comparisons expensive; differences are recalculated during display.
- Linked media is not independently archived.
- No restore interface, revision browser, backfill, or configuration screen is included.
- Tracking suppression contexts, direct SQL, and incompatible overrides can bypass tracking.
- The HTML formatter assumes snapshots use the Text columns; other HTML-tracking addons may conflict.
- Internal Odoo hooks and precommit metadata require review during upgrades.

This module provides operational change history. It does not provide an immutable audit ledger.

## Installation and Reuse

1. Add the addon directory to `addons_path`.
2. Restart Odoo and refresh the module list.
3. Install `oi_html_track`.
4. Add it to the integration addon’s dependencies.
5. Declare the required HTML fields with `html_track=True`.
6. Install or upgrade the integration addon.
7. Validate behavior in staging.

For a new business model, inherit `mail.thread`, define normal access controls, and include `<chatter/>` in its form view.

Custom tracking overrides must cooperate through `super()`.

## Validation

Syntax and isolated behavior/equivalence checks have passed. Full database integration, permissions, and large-document performance validation remain outstanding.

There is currently no bundled automated test suite.

Before production, validate:

- Adding, removing, replacing, filling, and clearing text.
- Formatting, image, and link changes.
- Multiple fields and multiple records.
- Restricted users and company-specific access rules.
- Existing tracking messages and notifications.
- Rollback and tracking-suppression contexts.
- Large or repetitive descriptions.