# OI HTML Tracking

Message-only tracking for selected HTML fields in Odoo 19.

- Technical name: `oi_html_track`
- Version: `19.0.0.0.0`
- Dependencies: `base`, `mail`

## Usage

Enable tracking on a stored HTML field belonging to a model that inherits
`mail.thread`:

    description = fields.Html(html_track=True)

Example integration:

    from odoo import fields, models

    class ProjectTask(models.Model):
        _inherit = "project.task"

        description = fields.Html(html_track=True)

The integration addon must depend on `project` and `oi_html_track`.
No application-specific tracking override is required.

## Behavior

| Change | Chatter message |
|---|---|
| Content added, edited, or partially deleted | Description updated. |
| Field completely cleared | Description removed. |
| Stored value unchanged | No message |
| Both values represent empty HTML | No message |

Multiple HTML-field messages are combined into one internal note per record.
Ordinary fields retain their normal tracking entries.

## Implementation

The addon extends `mail.thread` through three methods:

| Method | Responsibility |
|---|---|
| `_valid_field_parameter()` | Accepts `html_track` on HTML fields. |
| `_track_get_fields()` | Includes accessible, stored, marked HTML fields in native change capture. |
| `_mail_track()` | Separates marked HTML fields from native value tracking and posts updated/removed notes. |

Change detection compares the previous and current HTML strings.
`is_html_empty()` recognizes empty editor content such as `<p><br></p>`.

Messages are posted through `_message_log()`. Dynamic labels are escaped
using `Markup("<br/>").join(messages)`.

This version creates no new HTML snapshots or diff rows and requires no
`mail.tracking.value` extension.