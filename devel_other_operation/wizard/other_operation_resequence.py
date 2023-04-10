# Borrow logic from account resequence
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.date_utils import get_month, get_fiscal_year
from odoo.tools.misc import format_date

import re
from collections import defaultdict
import json


class OtherOperationReSequenceWizard(models.TransientModel):
    _name = 'other.operation.resequence.wizard'
    _description = 'Remake the sequence of Other Operation Service.'

    sequence_number_reset = fields.Char(compute='_compute_sequence_number_reset')
    first_date = fields.Date(help="Date (inclusive) from which the numbers are resequenced.")
    end_date = fields.Date(help="Date (inclusive) to which the numbers are resequenced. If not set, all Journal Entries up to the end of the period are resequenced.")
    first_name = fields.Char(compute="_compute_first_name", readonly=False, store=True, required=True, string="First New Sequence")
    ordering = fields.Selection([('keep', 'Keep current order'), ('date', 'Reorder by start date')], required=True, default='keep')
    other_operation_ids = fields.Many2many('other.operation')
    new_values = fields.Text(compute='_compute_new_values')
    preview_other_operations = fields.Text(compute='_compute_preview_other_operations')

    @api.model
    def default_get(self, fields_list):
        values = super(OtherOperationReSequenceWizard, self).default_get(fields_list)
        active_other_operation_ids = self.env['other.operation']
        if self.env.context['active_model'] == 'other.operation' and 'active_ids' in self.env.context:
            active_other_operation_ids = self.env['other.operation'].browse(self.env.context['active_ids'])
        if len(active_other_operation_ids.service_type_id) > 1:
            raise UserError(_('You can only resequence items from the same operation type'))

        values['other_operation_ids'] = [(6, 0, active_other_operation_ids.ids)]
        return values

    @api.depends('first_name')
    def _compute_sequence_number_reset(self):
        for record in self:
            record.sequence_number_reset = record.other_operation_ids[0]._deduce_sequence_number_reset(record.first_name)

    @api.depends('other_operation_ids')
    def _compute_first_name(self):
        self.first_name = ""
        for record in self:
            if record.other_operation_ids:
                record.first_name = min(record.other_operation_ids._origin.mapped('name'))

    @api.depends('new_values', 'ordering')
    def _compute_preview_other_operations(self):
        """Reduce the computed new_values to a smaller set to display in the preview."""
        for record in self:
            new_values = sorted(json.loads(record.new_values).values(), key=lambda x: x['server-date'], reverse=True)
            changeLines = []
            in_elipsis = 0
            previous_line = None
            for i, line in enumerate(new_values):
                if i < 3 or i == len(new_values) - 1 or line['new_by_name'] != line['new_by_date'] \
                 or (self.sequence_number_reset == 'year' and line['server-date'][0:4] != previous_line['server-date'][0:4])\
                 or (self.sequence_number_reset == 'month' and line['server-date'][0:7] != previous_line['server-date'][0:7]):
                    if in_elipsis:
                        changeLines.append({'id': 'other_' + str(line['id']), 'current_name': _('... (%s other)', in_elipsis), 'new_by_name': '...', 'new_by_date': '...', 'date': '...'})
                        in_elipsis = 0
                    changeLines.append(line)
                else:
                    in_elipsis += 1
                previous_line = line

            record.preview_other_operations = json.dumps({
                'ordering': record.ordering,
                'changeLines': changeLines,
            })

    @api.depends('first_name', 'other_operation_ids', 'sequence_number_reset')
    def _compute_new_values(self):
        """Compute the proposed new values.

        Sets a json string on new_values representing a dictionary thats maps other.operation
        ids to a disctionay containing the name if we execute the action, and information
        relative to the preview widget.
        """
        def _get_operation_key(other_operation_id):
            if self.sequence_number_reset == 'year':
                return other_operation_id.date.year
            elif self.sequence_number_reset == 'month':
                return (other_operation_id.date.year, other_operation_id.date.month)
            return 'default'

        self.new_values = "{}"
        for record in self.filtered('first_name'):
            operations_by_period = defaultdict(lambda: record.env['other.operation'])
            for operation in record.other_operation_ids._origin:  # Sort the operations by period depending on the sequence number reset
                operations_by_period[_get_operation_key(operation)] += operation

            format, format_values = self.env['other.operation']._get_sequence_format_param(record.first_name)

            new_values = {}
            for j, period_recs in enumerate(operations_by_period.values()):
                # compute the new values period by period
                for operation in period_recs:
                    new_values[operation.id] = {
                        'id': operation.id,
                        'current_name': operation.name,
                        'state': operation.state,
                        'date': format_date(self.env, operation.date),
                        'server-date': str(operation.date),
                    }

                new_name_list = [format.format(**{
                    **format_values,
                    'year': period_recs[0].date.year % (10 ** format_values['year_length']),
                    'month': period_recs[0].date.month,
                    'seq': i + (format_values['seq'] if j == (len(operations_by_period)-1) else 1),
                }) for i in range(len(period_recs))]

                # For all the operations of this period, assign the name by increasing initial name
                for operation, new_name in zip(period_recs.sorted(lambda m: (m.sequence_prefix, m.sequence_number)), new_name_list):
                    new_values[operation.id]['new_by_name'] = new_name
                # For all the operations of this period, assign the name by increasing date
                for operation, new_name in zip(period_recs.sorted(lambda m: (m.date, m.name, m.id)), new_name_list):
                    new_values[operation.id]['new_by_date'] = new_name

            record.new_values = json.dumps(new_values)

    def other_operation_resequence(self):
        new_values = json.loads(self.new_values)
        for other_operation_id in self.other_operation_ids:
            if str(other_operation_id.id) in new_values:
                if self.ordering == 'keep':
                    other_operation_id.name = new_values[str(other_operation_id.id)]['new_by_name']
                else:
                    other_operation_id.name = new_values[str(other_operation_id.id)]['new_by_date']
