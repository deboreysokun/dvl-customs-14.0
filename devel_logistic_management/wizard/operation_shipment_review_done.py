# -*- coding: utf-8 -*-
#############################################################################
#
#    Devel Logistics Co. Ltd
#
#    Copyrights 2018 Devellog. All Rights Reserved.(<https://devellog.com>)
#    Author: A2A Digital(<https://a2a-digital.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is belonged to Devel Logistics Co. Ltd
#
#############################################################################
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OperationShipmentReviewDone(models.TransientModel):
    _name = "operation.shipment.review.done"
    _description = "Operation Shipment Review Done"

    shipment_id = fields.Many2one(
        'operation.shipment', string='Shipment Ref.', required=True,
        default=lambda self: self.env.context.get('active_id', None),
    )
    review_comment = fields.Text(string="Comment")

    def action_review_done(self):
        original_context = self.env.context
        body_template = self.env.ref('devel_logistic_management.shipment_review_done')
        for record in self:
            model_description = self.env['ir.model']._get('operation.shipment').display_name
            body = body_template._render(
                dict(
                    record=record.shipment_id,
                    model_name ='operation.shipment',
                    res_id = record.shipment_id.id,
                    model_description=model_description,
                    comment = record.review_comment,
                    review_user = self.env.user.name,
                    access_link=self.env['mail.thread']._notify_get_action_link('view', model='operation.shipment', res_id=record.shipment_id.id),
                ),
                engine='ir.qweb',
                minimal_qcontext=True
            )
            record.shipment_id.message_notify(
                partner_ids= record.shipment_id.create_uid.partner_id.ids,
                body=body,
                subject=_('%(record_name)s: %(user_name)s has done reviewed your request operation.',
                    record_name=record.shipment_id.name,
                    user_name= self.env.user.name),
                record_name=record.shipment_id.name,
                model_description=model_description,
                email_layout_xmlid='mail.mail_notification_light',
            )

            body_template = body_template.with_context(original_context)
            self = self.with_context(original_context)
            record.shipment_id.write({
                'verify_user_id': self.env.uid,
                'verify_date': datetime.datetime.today().date(),
                'review_comment': record.review_comment,
                'review_done': True,
            })
