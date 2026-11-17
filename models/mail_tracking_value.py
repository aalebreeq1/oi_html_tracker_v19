from difflib import SequenceMatcher

from odoo import _, api, models
from odoo.tools.mail import html_to_inner_content


class MailTrackingValue(models.Model):
    _inherit = "mail.tracking.value"

    @api.model
    def _create_tracking_values(
        self, initial_value, new_value, col_name, col_info, record
    ):
        field = record._fields[col_name]

        if col_info["type"] == "html" and getattr(field, "html_track", False):
            # Keep complete HTML snapshots in native Text storage.
            col_info = dict(col_info, type="text")

        return super()._create_tracking_values( initial_value, new_value, col_name, col_info,record)

    @api.model
    def _get_html_tracking_diff(self, initial_value, new_value):
        old_text = html_to_inner_content(initial_value or "")
        new_text = html_to_inner_content(new_value or "")

        added = []
        removed = []

        matcher = SequenceMatcher(
            None, old_text, new_text, autojunk=False
        )

        for action, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            if action == "equal":
                continue

            old_part = old_text[old_start:old_end].strip()
            new_part = new_text[new_start:new_end].strip()

            if old_part:
                removed.append(old_part)

            if new_part:
                added.append(new_part)

        return old_text, " … ".join(added), " … ".join(removed)
    
    def _format_display_value(self, field_type, new=True):
        if field_type != "html":
            return super()._format_display_value(field_type, new=new)
        # The left side displays the complete previous text.
        if not new:
            return [
                html_to_inner_content(record.old_value_text or "") for record in self
            ]
        # The right side displays only added or removed fragments.
        result = []
        for record in self:
            old_text, added, removed = self._get_html_tracking_diff(
                record.old_value_text,
                record.new_value_text,
            )
            parts = []
            if added:
                parts.append(_("Added: %(text)s", text=added))
            if removed:
                parts.append(_("Removed: %(text)s", text=removed))
            result.append(" | ".join(parts) or _("HTML content updated."))
        return result