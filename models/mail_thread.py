from markupsafe import Markup

from odoo import _, models
from odoo.tools import ormcache


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _valid_field_parameter(self, field, name):
        if name == "html_track" and field.type == "html":
            return True

        return super()._valid_field_parameter(field, name)

    @ormcache("self.env.uid", "self.env.su")
    def _track_get_fields(self):
        tracked_fields = set(super()._track_get_fields())

        html_fields = {
            name
            for name, field in self._fields.items()
            if field.type == "html"
            and field.store
            and getattr(field, "html_track", False)
        }

        if html_fields:
            tracked_fields.update(
                self.fields_get(html_fields, attributes=())
            )

        return tracked_fields

    def _mail_track(self, tracked_fields, initial_values):
        changes, tracking_values = super()._mail_track(
            tracked_fields, initial_values
        )

        messages = []
        TrackingValue = self.env["mail.tracking.value"]

        for name in sorted(changes):
            field = self._fields[name]

            if (
                field.type != "html"
                or not field.store
                or not getattr(field, "html_track", False)
                or field.groups
            ):
                continue

            old_text, added, removed = (
                TrackingValue._get_html_tracking_diff(
                    initial_values[name],
                    self[name],
                )
            )

            label = tracked_fields[name]["string"]

            if added and removed:
                message = _(
                    "Text added and removed from %(field)s.",
                    field=label,
                )
            elif added:
                message = _(
                    "Text added to %(field)s.",
                    field=label,
                )
            elif removed:
                message = _(
                    "Text removed from %(field)s.",
                    field=label,
                )
            else:
                message = _(
                    "HTML content updated in %(field)s.",
                    field=label,
                )

            messages.append(message)

        if messages:
            # Preserve an existing application tracking message.
            pending_bodies = self.env.cr.precommit.data.get(
                f"mail.tracking.message.{self._name}",
                {},
            )

            if self.id in pending_bodies:
                existing_body = pending_bodies[self.id]
            else:
                existing_body = self._track_get_default_log_message(
                    changes
                )

            if existing_body:
                messages.insert(0, existing_body)

            # Escape dynamic text and separate multiple field messages.
            self._track_set_log_message(
                Markup("<br/>").join(messages)
            )

        return changes, tracking_values