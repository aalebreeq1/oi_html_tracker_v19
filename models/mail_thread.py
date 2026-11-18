from markupsafe import Markup

from odoo import _, models
from odoo.tools import ormcache
from odoo.tools.mail import is_html_empty

class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _valid_field_parameter(self, field, name):
        if name == "html_track" and field.type == "html":
            return True
        return super()._valid_field_parameter(field, name)

    @ormcache("self.env.uid", "self.env.su")
    def _track_get_fields(self):
        tracked_fields = set(super()._track_get_fields())
        html_fields = []
        for name, field in self._fields.items():
            if (
                field.type == "html"
                and field.store
                and getattr(field, "html_track", False)
            ):
                html_fields.append(name)
        if html_fields:
            tracked_fields.update(
                self.fields_get(html_fields, attributes=())
            )
        return tracked_fields

    def _mail_track(self, tracked_fields, initial_values):
        html_fields = []
        normal_fields = {}
        for name, info in tracked_fields.items():
            field = self._fields[name]
            if (
                field.type == "html"
                and field.store
                and getattr(field, "html_track", False)
            ):
                html_fields.append(name)
            else:
                normal_fields[name] = info
        changes, tracking_values = super()._mail_track(
            normal_fields, initial_values
        )
        messages = []
        for name in sorted(html_fields):
            if name not in initial_values or self._fields[name].groups:
                continue
            old_value = initial_values[name] or ""
            new_value = self[name] or ""
            if old_value == new_value:
                continue
            new_is_empty = is_html_empty(new_value)
            if new_is_empty and is_html_empty(old_value):
                continue
            label = tracked_fields[name]["string"]
            if new_is_empty:
                message = _("%(field)s removed.", field=label)
            else:
                message = _("%(field)s updated.", field=label)

            messages.append(message)
        if messages:
            self._message_log(
                body=Markup("<br/>").join(messages)
            )
        return changes, tracking_values