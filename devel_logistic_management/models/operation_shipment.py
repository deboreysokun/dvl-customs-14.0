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

import pytz
import base64
import datetime
from datetime import date, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import pdf
from odoo.modules.module import get_module_resource
from odoo.tools.misc import format_datetime

class OperationShipment(models.Model):
    _name = "operation.shipment"
    _order = "name desc, date desc, id desc"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Operation of Shipment"
    _check_company_auto = True

    @api.returns('self')
    def _default_stage(self):
        return self.env['operation.stage'].search([('name', '=', 'New')], limit=1)

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    active = fields.Boolean('Active', default=True, tracking=True)
    stage_id = fields.Many2one('operation.stage', string='Stage', index=True, tracking=True,
        readonly=False, store=True, default=_default_stage,
        copy=False, group_expand='_read_group_stage_ids', ondelete='restrict')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
            Override read_group to calculate the sum of the non-stored fields that depend on the user context
        """
        res = super(OperationShipment, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        shipments = self.env['operation.shipment']
        for shipment in res:
            if '__domain' in shipment:
                shipments = self.search(shipment['__domain'])
            if 'total_invoices' in fields:
                shipment['total_invoices'] = sum(shipments.mapped('total_invoices'))
            if 'tot_operation_expense' in fields:
                shipment['tot_operation_expense'] = sum(shipments.mapped('tot_operation_expense'))
            if 'balance' in fields:
                shipment['balance'] = sum(shipments.mapped('balance'))
            if 'total_cash_received' in fields:
                shipment['total_cash_received'] = sum(shipments.mapped('total_cash_received'))
            if 'total_expensed' in fields:
                shipment['total_expensed'] = sum(shipments.mapped('total_expensed'))
            if 'cash_balance' in fields:
                shipment['cash_balance'] = sum(shipments.mapped('cash_balance'))
            if 'total_deposit_amount' in fields:
                shipment['total_deposit_amount'] = sum(shipments.mapped('total_deposit_amount'))
            if 'balance_refund_amount' in fields:
                shipment['balance_refund_amount'] = sum(shipments.mapped('balance_refund_amount'))
            if 'refund_container_deposit_amount' in fields:
                shipment['refund_container_deposit_amount'] = sum(shipments.mapped('refund_container_deposit_amount'))
            if 'total_reimbursed' in fields:
                shipment['total_reimbursed'] = sum(shipments.mapped('total_reimbursed'))
        return res

    name = fields.Char(default=lambda self: _('New'),
            copy=False, readonly=True)
    date = fields.Date(default=fields.Date.context_today, copy=False)
    operation_type = fields.Selection(selection =[
                        ('import', 'Import'),
                        ('export', 'Export'),
                        ('transit', 'Transit')],
                        string='Type', tracking=True)
    transportation_mode = fields.Selection(selection =[
                        ('sea', 'By Sea'),
                        ('air', 'By Air'),
                        ('road', 'By Road'),
                        ('other', 'Others')],
                        string='Transportation', tracking=True, default='sea')
    shipment_type_id = fields.Many2one('shipment.type', tracking=True)
    shipper_id = fields.Many2one('res.partner', tracking=True)
    consignee_id = fields.Many2one('res.partner', tracking=True)
    notify_party_id = fields.Many2one('res.partner', tracking=True)
    customer_id = fields.Many2one('res.partner', tracking=True, string="Client")
    tag_ids = fields.Many2many('operation.tag', tracking=True)
    commodity = fields.Char(tracking=True)
    commodity_khmer = fields.Char(tracking=True)
    tax_calculation_id = fields.Many2one('tax.calculation', copy=False,tracking=True)
    entry_exit_port_id = fields.Many2one('entry.exit.port', string="Entry/Exit Port", tracking=True)
    exit_port_id = fields.Many2one('entry.exit.port', string="Exit Port", tracking=True) #For Transit Operation
    clearance_office_id = fields.Many2one('clearance.office', string="Clearance Office", tracking=True)
    valuation_office_id = fields.Many2one('clearance.office', string="Valuation Office", tracking=True)
    export_country_id = fields.Many2one('res.country', tracking=True)
    import_country_id = fields.Many2one('res.country', tracking=True)
    origin_country_id = fields.Many2one('res.country', string="Country of Origin", tracking=True)
    incoterm_id = fields.Many2one('account.incoterms', tracking=True)

    ##################### Carrier Infromation ########################
    bl_number = fields.Char(string='MBL N0.', tracking=True, copy=False)
    bl_date = fields.Date(string="BL Date", tracking=True, copy=False)
    hbl_number = fields.Char(string='HBL N0.', tracking=True, copy=False)
    hbl_date = fields.Date(string="HBL Date", tracking=True, copy=False)
    truck_bill_number = fields.Char(string='Truck Bill N0.', tracking=True, copy=False)
    truck_bill_date = fields.Date(string="Truck Bill Date", tracking=True, copy=False)
    container_number = fields.Text(string="Container Number", compute='get_container_lines', store=True)
    seal_number = fields.Text(compute='get_container_lines', store=True)
    container_qty_type = fields.Text(string="QTY", compute="get_container_lines", store=True) # display qty with type of container | 1 x 40HC
    internal_seal_number = fields.Char(string='Internal Seal N0.', tracking=True, copy=False)
    customs_seal_number = fields.Char(string='Customs Seal N0.', tracking=True, copy=False)
    etd = fields.Date(string="ETD", help='Estimated Time Departure', tracking=True, copy=False)
    eta = fields.Date(string="ETA",help='Estimated Time Arrival', tracking=True, copy=False)
    etr = fields.Date(string="ETR",help='Estimated Time Return', tracking=True, copy=False)
    co_loader_id = fields.Many2one('res.partner', tracking=True) # unused
    shipping_line_id = fields.Many2one('res.partner', tracking=True)
    port_of_loading_carrier = fields.Many2one('entry.exit.port', tracking=True)
    port_of_discharge_carrier = fields.Many2one('entry.exit.port', tracking=True)
    ##################### End of Carrier Information ########################
    # For Reporting Fields | Get POL POD of Carrier Else POL POD of Booking Order
    port_of_loading_report = fields.Many2one('entry.exit.port', store=True, compute="_compute_pol_pod_report", copy=False)
    port_of_discharge_report = fields.Many2one('entry.exit.port', store=True, compute="_compute_pol_pod_report", copy=False)

    ##################### Other Fields ########################
    verify_user_id = fields.Many2one('res.users', 'Review by',tracking=True,
        help='Person responsible for validating this check tax.')
    verify_date = fields.Date('Review Date',tracking=True, readonly=True)
    review_comment = fields.Text(string="Comment", readonly=True)
    to_review = fields.Boolean(default=False ,help="Request to Review Operation Work.")
    review_done = fields.Boolean(default=False)
    is_locked = fields.Boolean(default=False, help='Locked Operation! No more editable')
    internal_note = fields.Text('Latest Note', compute='_get_latest_internal_note_info')
    internal_note_lines = fields.One2many('shipment.internal.note', 'shipment_id', 'Note Lines', copy=False)
    ##################### End of Other Fields #####################################

    ########### Fields For Shipment Processing Status #############################
    docs_received = fields.Char(tracking=True, copy=False)
    cv = fields.Boolean(string="CV",tracking=True, copy=False)
    co = fields.Boolean(string="CO",tracking=True, copy=False)
    permit = fields.Boolean(tracking=True, copy=False)
    truck_bl = fields.Boolean(tracking=True, copy=False)
    inv_pl = fields.Boolean(tracking=True, copy=False)
    authorization = fields.Boolean(tracking=True, copy=False)
    list_co = fields.Boolean(tracking=True, copy=False)
    let_apply_co = fields.Boolean(tracking=True, copy=False)
    draft_custom_value = fields.Boolean(tracking=True, copy=False)
    check_doc = fields.Boolean(tracking=True, copy=False)
    submit = fields.Boolean(tracking=True, copy=False)
    cv_no = fields.Char(string="CV SAD NO",tracking=True, copy=False)
    co_no = fields.Char(string="CO SAD NO", tracking=True, copy=False)
    cv_1 = fields.Boolean(string="CV",tracking=True, copy=False)
    co_1 = fields.Boolean(string="CO",tracking=True, copy=False)

    docs_expire_date = fields.Date(tracking=True, copy=False)
    bl_sent_date = fields.Date(tracking=True, copy=False)
    arrival_sent = fields.Boolean(tracking=True, copy=False)
    ctn_arrival_port = fields.Date(string="Ctn Arrival Dry Port ",tracking=True, copy=False)

    do_delivery = fields.Date(tracking=True, copy=False)
    file_clearance_date = fields.Date(tracking=True, copy=False)
    delivery_date= fields.Char(tracking=True, copy=False, compute="get_trucking_info", store=True)
    truck_container = fields.Char(string="Truck and Container info", tracking=True, copy=False, compute='get_trucking_lines', store=True)
    driver_phone = fields.Char(tracking=True, copy=False, compute="get_trucking_lines", store=True)
    delivery_location = fields.Char(tracking=True, copy=False, compute="get_trucking_info", store=True)
    unloading_datetime = fields.Char(tracking=True, copy=False, compute="get_trucking_info", store=True)
    contact_info = fields.Char(tracking=True, copy=False)
    empty_return_to = fields.Char(string="Empty Return To Depo",tracking=True, copy=False, compute="get_trucking_info", store=True)
    empty_return_date = fields.Char(tracking=True, copy=False, compute="get_trucking_info", store=True)
    issued_invoice_date = fields.Date(copy=False,compute="_received_payment_date", store=True, compute_sudo=True)
    received_payment_date = fields.Date(copy=False,compute="_received_payment_date", store=True, compute_sudo=True)
    total_estimated_tax_amount = fields.Float(string="Estimated Tax", compute='_compute_total_estimated_tax_amount', store=True, help='Total Estimated Tax Amount. If has CO Form Number, it will get total CO tax amount. Otherwise, it get normal tax amount')
    reimbursement_date = fields.Date(copy=False,compute="_compute_reimbursement_date", store=True, compute_sudo=True)

    ########### End of Fields for Shipment Processing Status ######################

    ##################### Invoice and Packing List Fields ########################
    line_ids = fields.One2many('operation.shipment.item', 'shipment_id', 'INV and Packing List item', copy=True)
    total_gross_weight = fields.Float(compute='_compute_sum_quantity', tracking=True, store=True)
    gross_uom_id = fields.Many2one('uom.unit', tracking=True)
    total_net_weight = fields.Float(compute='_compute_sum_quantity', tracking=True)
    net_uom_id = fields.Many2one('uom.unit', tracking=True)
    total_qty = fields.Float(compute='_compute_sum_quantity', tracking=True)
    inv_qty_uom_id = fields.Many2one('uom.unit', string="INV QTY UOM", tracking=True)
    total_pl_qty = fields.Float(compute='_compute_sum_quantity', tracking=True)
    qty_uom_id = fields.Many2one('uom.unit',string="PL QTY UOM", tracking=True)
    total_amount = fields.Float(compute='_compute_sum_quantity', tracking=True, help='Total Amount')
    total_tax_amount = fields.Float(compute='_compute_sum_quantity', tracking=True, help='Total Customs Tax Amount before Apply CO')
    total_tax_amount_co = fields.Float(compute='_compute_sum_quantity', tracking=True, help='Total Customs Tax Amount After Apply CO')
    qty_text = fields.Char(help='Additional Text of QTY', tracking=True)
    inv_pack_date = fields.Date(tracking=True,copy=False)
    inv_pack_number = fields.Char(copy=False,tracking=True,help='Invoice and Packing List Number. If it is empty, it will take shipment number instead.')
    co_form_id = fields.Many2one('co.form', help='Certificate of Origin', tracking=True, string="CO Form")
    co_form_date = fields.Date(tracking=True)
    co_form_country_id = fields.Many2one('res.country',tracking=True)
    co_form_number = fields.Char(tracking=True, copy=True, string="CO Form N0.")
    customs_penalty_price = fields.Float(string="Customs Penalty", compute="_compute_custom_penalty_price",
        help='Penlty Unit Price to calculate Total Customs Penalty Charge for each containers in the List of Containers tab')
    penalty_rate_charge = fields.Float(tracking=True, string="Rate Charge", help='Customs Penalty Rate Charge')
    inv_packing_list_term = fields.Many2one('account.incoterms', tracking=True)
    ###Extra Fields for INV and Packing List Lines that are vehicle
    is_vehicle = fields.Boolean(string="Is Vehicle?",default=False)
    ###Extra Fields for INV and Packing List Lines that mix vehicle with other commodity
    mix_commodity = fields.Boolean(string="Mix Commodity?",default=False)

    copy_shipment_id = fields.Many2one('operation.shipment', domain="[('active', '=', True),('operation_type', '=', operation_type)]",
        string="Copy From Shipment", copy=False)
    copy_expense_line_id = fields.Many2one('operation.shipment', domain="[('active', '=', True),('operation_type', '=', operation_type)]",
        string="Copy Expense line form Shipment", copy=False)

    ##############Actual Amount Fields on Invoice and Packing List######################
    actual_gross_weight = fields.Float(tracking=True, compute='_compute_actual_gross_weight', readonly=False, store=True)
    actual_gross_uom_id = fields.Many2one('uom.unit', tracking=True, copy=False)
    actual_net_weight = fields.Float(tracking=True, copy=False)
    actual_net_uom_id = fields.Many2one('uom.unit', tracking=True, copy=False)
    actual_qty = fields.Float(tracking=True, copy=False)
    actual_qty_uom_id = fields.Many2one('uom.unit', tracking=True, copy=False)

    # Compute Actual Total Gross Weight on Shipment from List of Container
    @api.depends('container_line_ids.actual_gross_weight')
    def _compute_actual_gross_weight(self):
        for shipment in self:
            shipment.actual_gross_weight = sum(shipment.mapped('container_line_ids.actual_gross_weight') or [0.0])

    @api.depends('total_amount', 'penalty_rate_charge')
    def _compute_custom_penalty_price(self):
        for shipment in self:
            shipment.customs_penalty_price = shipment.total_amount * (shipment.penalty_rate_charge / 100)

    @api.onchange('copy_expense_line_id')
    def _onchange_copy_expense_line_id(self):
        if self.copy_expense_line_id:
            # Customs Valuation Office
            for line in self.copy_expense_line_id.expense_custom_permit_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.customs.office.permit'].new(copied_vals)
            # Shipping Line
            for line in self.copy_expense_line_id.expense_shipping_line_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.shipping.line'].new(copied_vals)
            # Customs Duty
            for line in self.copy_expense_line_id.expense_custom_duty_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.custom.duty'].new(copied_vals)
            # Clearance
            for line in self.copy_expense_line_id.expense_clearance_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.clearance'].new(copied_vals)
            # Port Charge
            for line in self.copy_expense_line_id.expense_port_charge_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.port.charge'].new(copied_vals)
            # Trucking
            for line in self.copy_expense_line_id.expense_trucking_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.trucking'].new(copied_vals)
            # Other Admin Expenses
            for line in self.copy_expense_line_id.expense_other_admin_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['shipment_id'] = self.id
                copied_vals['requester_user_id'] = self.env.user.id
                copied_vals['requested_date'] = fields.Datetime.now()
                new_line = self.env['shipment.expense.other.admin'].new(copied_vals)

    @api.onchange('copy_shipment_id')
    def _onchange_copy_shipment_id(self):
        for record in self:
            if self.copy_shipment_id:
                # copy data from other record;
                copied_vals = self.copy_shipment_id.copy_data()[0]
                record.write(copied_vals)

    @api.depends('port_of_loading_carrier', 'port_of_discharge_carrier', 'port_of_loading', 'port_of_discharge')
    def _compute_pol_pod_report(self):
        for shipment in self:
            shipment.port_of_loading_report = False
            shipment.port_of_discharge_report = False
            if shipment.port_of_loading_carrier:
                shipment.port_of_loading_report = shipment.port_of_loading_carrier.id or False
            else:
                shipment.port_of_loading_report = shipment.port_of_loading.id or False

            if shipment.port_of_discharge_carrier:
                shipment.port_of_discharge_report = shipment.port_of_discharge_carrier.id or False
            else:
                shipment.port_of_discharge_report = shipment.port_of_discharge.id or False


    ######################## Fields for No Consignee Stamp ###############################
    inv_pl_stamp_consignee = fields.Boolean(string="Consignee Stamp?", copy=False)
    auth_trader_stamp_consignee = fields.Boolean(string="Consignee Stamp?", copy=False)
    permit_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    req_letter_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    gua_letter_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    vgm_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    draft_bl_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    list_cont_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    truck_bill_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    auth_broker_stamp_consignee  = fields.Boolean(string="Consignee Stamp?", copy=False)
    # Note: Other fields ended with _stamp is for shipper stamp
    ########################import documents#############################################
    co_doc = fields.Boolean(copy=False, tracking=True)
    co_attactment_doc = fields.Boolean(copy=False, tracking=True)
    inv_packing_doc = fields.Boolean(copy=False, tracking=True)
    inv_pl_stamp = fields.Boolean(copy=False, tracking=True) # true print document without shipper stamp&sign
    authorization_doc = fields.Boolean(copy=False, tracking=True) # Authorization Trader
    auth_trader_stamp = fields.Boolean(copy=False, tracking=True)
    authorized_emp_id = fields.Many2one('res.partner', string="AUTH Employee", help="អ្នកទទួលសិទ្ធ", tracking=True)
    owner_id = fields.Many2one('res.partner', string="Company's Owner", help="អ្នកផ្ទេរសិទ្ធ", tracking=True)
    customs_emp_id = fields.Many2one('res.partner', string="Customs Borker", help="ជើងសាគយ", tracking=True)
    province_id = fields.Many2one('province.city', help="ធ្វើនៅ....." , tracking=True)
    document_date = fields.Date(tracking=True)
    khmer_date_char = fields.Char()
    permit_doc = fields.Boolean(copy=False, tracking=True)
    permit_stamp = fields.Boolean(copy=False, tracking=True)

    ###############################export documents###################################
    booking_order_doc = fields.Boolean(copy=False, tracking=True)
    export_inv_packing_doc = fields.Boolean(copy=False, tracking=True)
    export_requirement_letter = fields.Boolean(copy=False, tracking=True)
    req_letter_stamp = fields.Boolean(copy=False, tracking=True)
    commodity_source = fields.Selection(string="ប្រភពទំនិញ", selection =[('produce', 'ផលិត'),('recycle', 'កែច្នៃ'),('buy', 'ប្រមូលទិញ')],default='produce',tracking=True)
    company_type = fields.Selection(string="ប្រភេទក្រុមហ៊ុន", selection =[('company', 'ក្រុមហ៊ុន'),('factory', 'រោងចក្រ')], default='company', tracking=True)
    guaranteed_letter = fields.Boolean(copy=False, tracking=True)
    gua_letter_stamp = fields.Boolean(copy=False, tracking=True)
    vgm = fields.Boolean(copy=False, tracking=True)
    vgm_stamp = fields.Boolean(copy=False, tracking=True)
    draft_bl = fields.Boolean(copy=False, tracking=True)
    draft_bl_stamp= fields.Boolean(copy=False, tracking=True)
    inspection_doc = fields.Boolean(copy=False)
    list_of_container = fields.Boolean(copy=False)
    list_cont_stamp = fields.Boolean(copy=False)
    inspection_fixed_doc = fields.Boolean(copy=False)

    ###########################transit documents###################################
    transit_inv_packing_doc = fields.Boolean(copy=False, tracking=True)
    transit_truck_bill_doc = fields.Boolean(copy=False, tracking=True)
    truck_bill_stamp = fields.Boolean(copy=False, tracking=True)
    transit_authorization_doc = fields.Boolean(copy=False, tracking=True) # Authorization Broker
    auth_broker_stamp = fields.Boolean(copy=False, tracking=True)

    ############################## Cash Advance #############################
    cash_advance_line_ids = fields.One2many('operation.cash.advance', 'shipment_id', 'Cash Advance Lines', copy=False)
    total_cash_advance_amount = fields.Monetary(currency_field='company_currency_id', compute='_compute_total_cash_advance', string="Total Cash Advance",
            groups='account.group_account_invoice,account.group_account_readonly', store=True, copy=False)
    total_cash_advance_paid = fields.Monetary(currency_field='company_currency_id', compute='_compute_total_cash_advance', string="Advance Paid",
        groups='account.group_account_invoice,account.group_account_readonly', store=True, copy=False)
    total_cash_advance_cleared = fields.Monetary(currency_field='company_currency_id', string="Advance Cleared", readonly=True, store=True ,compute='_compute_total_cash_advance_cleared',
        groups='account.group_account_invoice,account.group_account_readonly')
    total_cash_advance_remaining = fields.Monetary(currency_field='company_currency_id', string="Advance Remaining", compute='_compute_total_cash_advance_remaining',
        groups='account.group_account_invoice,account.group_account_readonly', store=True, copy=False)

    ############################## End of Accounting documents#############################

    ##############################Accounting documents#############################
    cover_file = fields.Boolean(copy=False, tracking=True)
    cash_payment = fields.Boolean(copy=False, tracking=True)
    closing_file = fields.Boolean(copy=False, tracking=True)

    ############################### Booking Order and Truck Bill Of Lading ################################
    booking_date = fields.Date(tracking=True, copy=False)
    description_of_goods = fields.Text(string="Description of Goods", tracking=True)
    volume_cbm = fields.Char(string="Volume / CBM", tracking=True)
    pick_up_date = fields.Date(help="Pick up date of Empty Containers", tracking=True, copy=False)
    place_of_reciept = fields.Many2one('entry.exit.port', tracking=True)
    port_of_loading = fields.Many2one('entry.exit.port', tracking=True)
    port_of_discharge = fields.Many2one('entry.exit.port', tracking=True)
    port_of_delivery = fields.Many2one('entry.exit.port', string="Port of Delivery", tracking=True)
    final_destination = fields.Many2one('entry.exit.port', string="Final Destination", tracking=True)
    vessel_id = fields.Char(tracking=True, copy=False)
    voyage_number = fields.Char(tracking=True, copy=False)
    vessel_voyage_info = fields.Char(string="Vessel/Voyage", store=True, compute="_compute_vessel_voyage_info",copy=False)
    booking_ship_number = fields.Char(tracking=True, copy=False) # unused
    freight = fields.Selection(selection =[('prepaid', 'PREPAID'),('collect', 'COLLECT')],default='prepaid',tracking=True)
    etd_export_port = fields.Many2one('entry.exit.port', tracking=True, copy=False)
    etd_export_date = fields.Date(tracking=True, copy=False)
    eta_export_port = fields.Many2one('entry.exit.port', tracking=True, copy=False)
    eta_export_date = fields.Date(string="ETA Final Destination port",tracking=True, copy=False)
    #Transit Operation need these fields (eg. Malaysia --> Singapore --> Camboida)
    etd_export_port_1 = fields.Many2one('entry.exit.port', tracking=True, copy=False)
    etd_export_date_1 = fields.Date(tracking=True, copy=False)
    eta_export_port_1 = fields.Many2one('entry.exit.port', tracking=True, copy=False)
    eta_export_date_1 = fields.Date(tracking=True, copy=False)
    ###############################END of Booking Order################################

    truck_line_ids = fields.One2many('truck.booking', 'shipment_id', 'Truck Booking', tracking=True)
    num_of_truck = fields.Integer(string="Number of Truck", help="Number of Truck for qty of container")

    ############################### Lis of Container ################################
    container_line_ids = fields.One2many('shipment.container', 'shipment_id', 'Container items')
    total_container_qty = fields.Float(string="CTNR QTY", store=True,compute='_compute_total_amount')
    total_empty_weight = fields.Float('Total Container Empty Weight', store=True ,compute='_compute_total_amount')
    total_container_gross_weight = fields.Float('Total Container Gross Weight', store=True ,compute='_compute_total_amount')

    total_deposit_amount = fields.Float('Total Deposit Amount', store=True ,compute='_compute_total_amount')
    container_deposit_qty = fields.Float(string="Deposit Qty", tracking=True, copy=False)
    container_deposit_date = fields.Date('Deposit Date', tracking=True, copy=False)
    container_deposit_move_id = fields.Many2one('account.move', string="Journal Entry", tracking=True, copy=False)

    refund_container_deposit_qty = fields.Float(string="Refund Deposit Qty", tracking=True, copy=False)
    refund_container_deposit_amount = fields.Float('Total Refund Amount' , readonly=True, copy=False, compute="_compute_total_refund_deposit_amount", compute_sudo=True)

    refund_container_remain_amount = fields.Float('Remaining Refund Amount' , readonly=True, copy=False, compute="_compute_refund_container_remaining_amount", store=True)
    deposit_and_refund_amount_equal = fields.Boolean(default=False, copy=False, compute="_compute_refund_container_remaining_amount", compute_sudo=True)

    @api.depends('total_deposit_amount', 'refund_container_deposit_amount')
    def _compute_refund_container_remaining_amount(self):
        for shipment in self:
            shipment.refund_container_remain_amount = shipment.total_deposit_amount - shipment.refund_container_deposit_amount
            if shipment.refund_container_deposit_amount == shipment.total_deposit_amount:
                shipment.deposit_and_refund_amount_equal = True
            elif shipment.refund_container_deposit_amount == 0.0:
                shipment.refund_container_remain_amount = 0
                shipment.refund_container_deposit_qty = 0
                shipment.deposit_and_refund_amount_equal = False
            else:
                shipment.deposit_and_refund_amount_equal = False

    @api.depends('refund_container_deposit_move_ids')
    def _compute_total_refund_deposit_amount(self):
        for shipment in self:
            shipment.refund_container_deposit_amount = 0
            domain = [('move_id', 'in', shipment.refund_container_deposit_move_ids.ids),
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('move_id.move_type', '=', 'entry'),
                ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id),
            ]
            debits = self.env['account.move.line'].read_group(domain, ['debit'], ['move_id'])
            credits = self.env['account.move.line'].read_group(domain, ['credit'], ['move_id'])
            shipment.refund_container_deposit_amount = sum(amount['debit'] for amount in debits) - sum(amount['credit'] for amount in credits)

    refund_container_deposit_date = fields.Date('Refund Date',tracking=True, copy=False)
    refund_container_deposit_move_ids = fields.Many2many('account.move', string="Journal Entry", copy=False)
    balance_refund_amount = fields.Monetary(currency_field='company_currency_id', readonly=False, compute='_compute_balance_refund_amount')

    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id')

    @api.constrains('total_container_gross_weight', 'total_gross_weight')
    def _constrains_total_gross_weight(self):
        for shipment in self:
            if shipment.total_container_gross_weight > 0 and shipment.total_gross_weight > 0:
                if shipment.total_container_gross_weight != shipment.total_gross_weight:
                    raise UserError(_(
                        "Total Gross Weight of Container %s doesn't equal to %s Total Gross Weight of INV and Packing List!") % (self.total_container_gross_weight, self.total_gross_weight))

    # List of Container -  Container Total Amount and  Tot. Empyt Weight
    @api.depends('container_line_ids.unit_price','container_line_ids.weight','container_line_ids.gross_weight')
    def _compute_total_amount(self):
        for shipment in self:
            total_deposit_amount = total_deposit_qty = total_empty_weight = container_qty = tot_cont_gw = 0
            for line in shipment.container_line_ids:
                total_deposit_amount += line.unit_price
                total_empty_weight += line.weight
                tot_cont_gw += line.gross_weight
                container_qty += 1
                if line.unit_price != 0.0:
                    total_deposit_qty += 1
            shipment.total_deposit_amount = total_deposit_amount
            shipment.container_deposit_qty = total_deposit_qty
            shipment.total_empty_weight = total_empty_weight
            shipment.total_container_gross_weight = tot_cont_gw
            shipment.total_container_qty = container_qty

    @api.depends('total_deposit_amount','refund_container_deposit_amount')
    def _compute_balance_refund_amount(self):
        for shipment in self:
            shipment.balance_refund_amount = shipment.total_deposit_amount - shipment.refund_container_deposit_amount

    @api.depends('vessel_id', 'voyage_number')
    def _compute_vessel_voyage_info(self):
        for shipment in self:
            shipment.vessel_voyage_info = False
            shipment.vessel_voyage_info = shipment.vessel_id or ''
            if shipment.voyage_number:
                shipment.vessel_voyage_info += '/' + shipment.voyage_number

    ############### Attachment for Operation Documents #############
    attachment_operation_number = fields.Integer(compute='_compute_attachment_operation_number', string='Number of Operation Attachments')
    def _compute_attachment_operation_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'operation.shipment'), ('accounting_document', '=', False), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for shipment in self:
            shipment.attachment_operation_number = attachment.get(shipment.id, 0)
    def action_get_attachment_operation_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'operation.shipment'), ('res_id', 'in', self.ids),('accounting_document', '=', False)]
        res['context'] = {'default_res_model': 'operation.shipment', 'default_res_id': self.id}
        return res
    ############### Attachment for Accounting Documents and Operation Document #############
    attachment_accounting_number = fields.Integer(compute='_compute_attachment_accounting_number', string='Number of All Attachments')
    def _compute_attachment_accounting_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'operation.shipment'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for shipment in self:
            shipment.attachment_accounting_number = attachment.get(shipment.id, 0)
    def action_get_attachment_accounting_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'operation.shipment'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'operation.shipment', 'default_res_id': self.id, 'default_accounting_document': True}
        return res

    @api.model
    def confirm_expense_lines(self, selected_ids, model):
        orderline_sudo = self.env[model]
        order_lines = orderline_sudo.browse(selected_ids)
        for line in order_lines:
            line.action_confirm()
        return True

    @api.model
    def approve_expense_lines(self, selected_ids, model):
        orderline_sudo = self.env[model]
        order_lines = orderline_sudo.browse(selected_ids)
        for line in order_lines:
            line.action_approve()
        return True

    @api.model
    def draft_expense_lines(self, selected_ids, model):
        orderline_sudo = self.env[model]
        order_lines = orderline_sudo.browse(selected_ids)
        for line in order_lines:
            line.action_draft_user_confirm()
        return True

    @api.model
    def confirm_and_approve(self, selected_ids, model):
        orderline_sudo = self.env[model]
        order_lines = orderline_sudo.browse(selected_ids)
        for line in order_lines:
            line.action_confirm_approve()
        return True

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        for shipment in self:
            if shipment.stage_id.is_done == True:
                shipment.write({'is_locked': True})
            else:
                shipment.write({'is_locked': False})

    #Customs Valuation / Customs Permit Expenses Lines
    expense_custom_permit_line_ids = fields.One2many('shipment.expense.customs.office.permit', 'shipment_id', 'Expense Custom Office/Permit Lines', tracking=True, copy=False)
    total_custom_permit_amount = fields.Float('Total Paid', compute='_compute_total_custom_permit_amount', tracking=True)
    tot_custom_permit_lines = fields.Float('Total Expense', compute='_compute_total_custom_permit_lines')

    @api.depends('expense_custom_permit_line_ids.sub_total')
    def _compute_total_custom_permit_amount(self):
        for shipment in self:
            total_custom_permit_amount = 0
            for line in shipment.expense_custom_permit_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_custom_permit_amount += line.sub_total
            shipment.total_custom_permit_amount = total_custom_permit_amount

    @api.depends('expense_custom_permit_line_ids.sub_total')
    def _compute_total_custom_permit_lines(self):
        for shipment in self:
            total_custom_permit_lines = 0
            for line in shipment.expense_custom_permit_line_ids.filtered(lambda l: l.state != 'reject'):
                total_custom_permit_lines += line.sub_total
            shipment.tot_custom_permit_lines = total_custom_permit_lines

    # Shipping Line Expenses
    expense_shipping_line_line_ids = fields.One2many('shipment.expense.shipping.line', 'shipment_id', 'Expense Shipping Lines', copy=False)
    total_shipping_line_amount = fields.Float('Total Amount', compute='_compute_total_shipping_line_amount', tracking=True)
    total_thc_amount = fields.Float('THC Amount', compute='_compute_total_thc_amount')
    total_thc_paid_date = fields.Date(string="THC Paid Date", compute='_compute_total_thc_amount')
    tot_shipping_line_lines = fields.Float('Total Expense', compute='_compute_total_shipping_line_lines')

    @api.depends('expense_shipping_line_line_ids.sub_total')
    def _compute_total_shipping_line_amount(self):
        for shipment in self:
            total_shipping_line_amount = 0
            lines = shipment.expense_shipping_line_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid'])
            for line in lines:
                total_shipping_line_amount += line.sub_total
            shipment.total_shipping_line_amount = total_shipping_line_amount

    @api.depends('expense_shipping_line_line_ids.sub_total')
    def _compute_total_shipping_line_lines(self):
        for shipment in self:
            total_shipping_line_lines = 0
            #19-Other Receivable(newly created in this app) excluded deposit&refund container and status reject
            lines = shipment.expense_shipping_line_line_ids.filtered(lambda l: l.state != 'reject' and l.account_id.user_type_id.id != 19)
            for line in lines:
                total_shipping_line_lines += line.sub_total
            shipment.tot_shipping_line_lines = total_shipping_line_lines

    @api.onchange('expense_shipping_line_line_ids.thc_amount')
    def _compute_total_thc_amount(self):
        for shipment in self:
            total_thc_amount = 0
            thc_paid_date = False
            for line in shipment.expense_shipping_line_line_ids:
                if line.thc_amount == True:
                    total_thc_amount += line.sub_total
                if line.thc_amount == True and line.state in ['paid', 'direct_paid']:
                    thc_paid_date = line.paid_date
            shipment.total_thc_amount = total_thc_amount
            shipment.total_thc_paid_date = thc_paid_date

    #Clearance Expenses
    expense_clearance_line_ids = fields.One2many('shipment.expense.clearance', 'shipment_id', 'Expense Clearance Lines', copy=False)
    total_clearance_amount = fields.Float('Total Amount', compute='_compute_total_clearance_amount')
    tot_clearance_lines = fields.Float('Total Expense', compute='_compute_total_clearance_lines')

    @api.depends('expense_clearance_line_ids.sub_total')
    def _compute_total_clearance_amount(self):
        for shipment in self:
            total_clearance_amount = 0
            for line in shipment.expense_clearance_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_clearance_amount += line.sub_total
            shipment.total_clearance_amount = total_clearance_amount

    @api.depends('expense_clearance_line_ids.sub_total')
    def _compute_total_clearance_lines(self):
        for shipment in self:
            total_clearance_lines = 0
            for line in shipment.expense_clearance_line_ids.filtered(lambda l: l.state != 'reject'):
                total_clearance_lines += line.sub_total
            shipment.tot_clearance_lines = total_clearance_lines

    #Custom Duty Expenses
    expense_custom_duty_line_ids = fields.One2many('shipment.expense.custom.duty', 'shipment_id', 'Expense Custom Duty Lines', copy=False)
    total_custom_duty_amount = fields.Float('Total Amount', compute='_compute_total_custom_duty_amount', tracking=True)
    total_duty_tax = fields.Float('Duty Tax Amount', compute='_compute_total_duty_amount')
    total_duty_tax_khr = fields.Float('Duty Tax Amount in KHR', compute='_compute_total_duty_amount')
    customs_exchange_rate = fields.Float('Exchange Rate', copy=False)
    total_duty_tax_paid_date = fields.Date('Duty Tax Paid Date', compute='_compute_total_duty_amount')
    tot_custom_duty_lines = fields.Float('Total Expense', compute='_compute_total_custom_duty_lines')

    #Total Customs Duty Expnese Line Paid Amount
    @api.depends('expense_custom_duty_line_ids.sub_total')
    def _compute_total_custom_duty_amount(self):
        for shipment in self:
            total_custom_duty_amount = 0
            for line in shipment.expense_custom_duty_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_custom_duty_amount += line.sub_total
            shipment.total_custom_duty_amount = total_custom_duty_amount

    @api.depends('expense_custom_duty_line_ids.sub_total')
    def _compute_total_custom_duty_lines(self):
        for shipment in self:
            total_custom_duty_lines = 0
            for line in shipment.expense_custom_duty_line_ids.filtered(lambda l: l.state != 'reject'):
                total_custom_duty_lines += line.sub_total
            shipment.tot_custom_duty_lines = total_custom_duty_lines

    #Total Duty Tax Amount in KHR
    @api.onchange('expense_custom_duty_line_ids.duty_tax', 'customs_exchange_rate')
    def _compute_total_duty_amount(self):
        for shipment in self:
            total_duty_tax = 0
            duty_tax_paid_date = False
            for line in shipment.expense_custom_duty_line_ids:
                if line.duty_tax == True:
                    total_duty_tax += line.sub_total
                if line.duty_tax == True and line.state in ['paid', 'direct_paid']:
                    duty_tax_paid_date = line.paid_date
            shipment.total_duty_tax_paid_date = duty_tax_paid_date
            shipment.total_duty_tax = total_duty_tax
            shipment.total_duty_tax_khr = shipment.total_duty_tax *shipment.customs_exchange_rate

    # Port Charge Expense
    expense_port_charge_line_ids = fields.One2many('shipment.expense.port.charge', 'shipment_id', 'Expense Port Charge Lines', copy=False)
    total_port_charge_amount = fields.Float('Total Amount', compute='_compute_total_port_charge_amount')
    tot_port_charge_lines = fields.Float('Total Expense', compute='_compute_total_port_charge_lines')

    #total lines exclude reject state: Total Expense
    @api.depends('expense_port_charge_line_ids.sub_total')
    def _compute_total_port_charge_lines(self):
        for shipment in self:
            total_port_charge_lines = 0
            for line in shipment.expense_port_charge_line_ids.filtered(lambda l: l.state != 'reject'):
                total_port_charge_lines += line.sub_total
            shipment.tot_port_charge_lines = total_port_charge_lines

    #total paid Lines: Total Paid
    @api.depends('expense_port_charge_line_ids.sub_total')
    def _compute_total_port_charge_amount(self):
        for shipment in self:
            total_port_charge_amount = 0
            for line in shipment.expense_port_charge_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_port_charge_amount += line.sub_total
            shipment.total_port_charge_amount = total_port_charge_amount

    # Trcuking Line Expenses
    expense_trucking_line_ids = fields.One2many('shipment.expense.trucking', 'shipment_id', 'Expense Trucking Lines', copy=False)
    total_trucking_amount = fields.Float('Total Amount', compute='_compute_total_trucking_amount')
    tot_trucking_lines = fields.Float('Total Expense', compute='_compute_total_trucking_lines')

    #total lines exclude reject state: Total Expense
    @api.depends('expense_trucking_line_ids.sub_total')
    def _compute_total_trucking_lines(self):
        for shipment in self:
            total_trucking_lines = 0
            for line in shipment.expense_trucking_line_ids.filtered(lambda l: l.state != 'reject'):
                total_trucking_lines += line.sub_total
            shipment.tot_trucking_lines = total_trucking_lines

    #total paid Lines: Total Paid
    @api.depends('expense_trucking_line_ids.sub_total')
    def _compute_total_trucking_amount(self):
        for shipment in self:
            total_trucking_amount = 0
            for line in shipment.expense_trucking_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_trucking_amount += line.sub_total
            shipment.total_trucking_amount = total_trucking_amount

    # Other Admin Expenses
    expense_other_admin_line_ids = fields.One2many('shipment.expense.other.admin', 'shipment_id', copy=False)
    total_other_admin_amount = fields.Float('Total Amount', compute='_compute_total_other_admin_amount')
    tot_other_admin_lines = fields.Float('Total Expense', compute='_compute_total_other_admin_lines')

    #total lines exclude reject state: Total Expense
    @api.depends('expense_other_admin_line_ids.sub_total')
    def _compute_total_other_admin_lines(self):
        for shipment in self:
            total_other_admin_lines = 0
            for line in shipment.expense_other_admin_line_ids.filtered(lambda l: l.state != 'reject'):
                total_other_admin_lines += line.sub_total
            shipment.tot_other_admin_lines = total_other_admin_lines

    #total paid Lines: Total Paid
    @api.depends('expense_other_admin_line_ids.sub_total')
    def _compute_total_other_admin_amount(self):
        for shipment in self:
            total_other_admin_amount = 0
            for line in shipment.expense_other_admin_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_other_admin_amount += line.sub_total
            shipment.total_other_admin_amount = total_other_admin_amount

    #====================== Revenue and Expense Section =================================
    # Get all Total Cash Paid of each shipments in account.move.line # (minus sign)
    total_expensed = fields.Monetary(currency_field='company_currency_id',compute='_expense_total', string="Total Cash Paid",
    groups='account.group_account_invoice,account.group_account_readonly')

    # Total Cash Paid
    def _expense_total(self):
        for record in self:
            record.total_expensed = 0
            if not self.ids:
                return True
            cash_paid = 0
            cash_out_bill_domain = [
                ('shipment_id', '=', record.id),
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', 'in', ['in_invoice', 'out_refund']),
            ]
            cash_out_bill_ids = self.env['account.move'].search(cash_out_bill_domain)
            for bill_id in cash_out_bill_ids:
                cash_paid += abs(bill_id.amount_total_signed) - abs(bill_id.amount_residual_signed) # return positive number
            domain = [
                ('shipment_id', '=', record.id), # Adjust this
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('move_id.move_type', 'not in', ['in_invoice','in_refund', 'out_invoice', 'out_refund' 'out_receipt']),
                ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id),
            ]
            credit = self.env['account.move.line'].read_group(domain, ['credit'], ['move_id'])
            cash_paid += sum(amount['credit'] for amount in credit) #since it's cash paid; get credit side only
            record.total_expensed = - cash_paid

    def _get_bill_ids(self):
        bill_payment_info = {}
        bill_payment_ids = []
        payment_account_move_ids = []
        all_bill_ids = []

        domain = [ ('shipment_id', '=', self.id), ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('in_invoice', 'out_refund'))]
        bill_ids = self.env['account.move'].search(domain)

        if bill_ids:
            for bill_id in bill_ids:
                all_bill_ids.append(bill_id)

        for bill_id in all_bill_ids:
            bill_payment_info = bill_id._get_reconciled_info_JSON_values()
            for payment_vals in bill_payment_info:
                payment_id = self.env['account.payment'].browse(payment_vals['account_payment_id'])
                bill_payment_ids.append(payment_id)

        for payment_id in bill_payment_ids:
            payment_account_move_ids.append(payment_id.move_id.id)

        return payment_account_move_ids

    def action_view_cash_paid_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")
        account_move_ids = self._get_bill_ids() or []
        action['domain'] = ["|", ('move_id', 'in', account_move_ids),
            ('shipment_id', '=', self.id), # Adjust this
            '&', ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ['entry']),
            ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id),
        ]
        return action

    # Total Reimbursed Invoice + Total Reimbursed Bill
    total_reimbursed= fields.Monetary(currency_field='company_currency_id',compute='_total_reimbursed', string="Reimbursed",
        groups='account.group_account_invoice,account.group_account_readonly')

    def _total_reimbursed(self):
        for record in self:
            record.total_reimbursed = 0
            if not self.ids:
                return True
            domain = [
                ('shipment_id', '=', record.id),
                ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')),
                ('journal_id.is_reimbursement', '=', True),
            ]
            price_totals = self.env['account.move'].read_group(domain, ['amount_total_signed'], ['shipment_id'])
            record.total_reimbursed = sum(amount['amount_total_signed'] for amount in price_totals)

    # Get all Total Reimbursement Invoice Type
    total_reimbursed_invoice = fields.Monetary(currency_field='company_currency_id',compute='_total_reimbursed_invoice', string="Receive Reimbursed",
        groups='account.group_account_invoice,account.group_account_readonly')

    def _total_reimbursed_invoice(self):
        for record in self:
            record.total_reimbursed_invoice = 0
            if not self.ids:
                return True
            domain = [
                ('shipment_id', '=', record.id),
                ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('journal_id.is_reimbursement', '=', True),
            ]
            # Here we use amount_residual_signed because we want the amount to be 0 when reimbursement invoice is paid.
            price_totals = self.env['account.move'].read_group(domain, ['amount_residual_signed'], ['shipment_id'])
            record.total_reimbursed_invoice = sum(amount['amount_residual_signed'] for amount in price_totals)

    def action_view_reimbursed_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("devel_logistic_management.action_reimbursement_invoice_type")
        action['domain'] = [
            ('shipment_id', '=', self.id),
            ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('journal_id.is_reimbursement', '=', True),
        ]
        journal_id = self.env['account.journal'].search([('is_reimbursement', '=', True),('type', '=', 'sale')], limit=1)
        action['context'] = {
            'default_move_type': 'out_invoice',
            'default_shipment_id': self.id,
            'default_partner_id': self.customer_id.id,
            'default_is_reimbursement_invoice': True,
            'default_journal_id': journal_id.id,
        }
        return action

    # Get all Total Reimbursement Bill Type
    total_reimbursed_reciept = fields.Monetary(currency_field='company_currency_id',compute='_total_reimbursed_reciept', string="Pay Reimbursed",
        groups='account.group_account_invoice,account.group_account_readonly')

    def _total_reimbursed_reciept(self):
        for record in self:
            record.total_reimbursed_reciept = 0
            if not self.ids:
                return True
            domain = [
                ('shipment_id', '=', record.id),
                ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('in_invoice', 'in_refund')),
                ('journal_id.is_reimbursement', '=', True),
            ]
            # Here we use amount_residual_signed because we want the amount to be 0 when reimbursement invoice is paid.
            price_totals = self.env['account.move'].read_group(domain, ['amount_residual_signed'], ['shipment_id'])
            record.total_reimbursed_reciept = sum(amount['amount_residual_signed'] for amount in price_totals)

    def action_view_reimbursed_reciept(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("devel_logistic_management.action_reimbursement_bill_type")
        action['domain'] = [
            ('shipment_id', '=', self.id),
            ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('journal_id.is_reimbursement', '=', True),
        ]
        journal_id = self.env['account.journal'].search([('is_reimbursement', '=', True),('type', '=', 'purchase')], limit=1)

        action['context'] = {
            'default_move_type': 'in_invoice',
            'default_shipment_id': self.id,
            'default_partner_id': self.customer_id.id,
            'default_is_reimbursement_invoice': True,
            'default_journal_id': journal_id.id,
        }
        return action

    # Get all Total Invoice of each shipments
    total_invoices = fields.Monetary(currency_field='company_currency_id',compute='_total_invoices', string="Total Invoices",
    groups='account.group_account_invoice,account.group_account_readonly')
    invoice_ids = fields.One2many(string='Related Invoices', inverse_name='shipment_id', comodel_name='account.move',
        domain=[('state', '=', 'posted'),('move_type', 'in', ['out_invoice', 'out_refund']), ('journal_id.is_reimbursement', '=', False)])
    total_cash_received = fields.Monetary(currency_field='company_currency_id',compute='compute_total_cash_received', string="Total Cash Received",
    groups='account.group_account_invoice,account.group_account_readonly')

    # Total Cash Received
    def compute_total_cash_received(self):
        for shipment in self:
            cash_received = 0
            domain = [('shipment_id', '=', shipment.id),
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', 'in', ['out_invoice', 'in_refund'])]
            invoice_ids = self.env['account.move'].search(domain)

            if invoice_ids:
                for inv_id in invoice_ids:
                    cash_received += inv_id.amount_total_signed - inv_id.amount_residual_signed
            domain = [
                ('move_id.shipment_id', '=', shipment.id),
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('move_id.move_type', 'not in', ['in_invoice', 'in_refund', 'out_invoice', 'out_refund', 'in_receipt']),
                ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id), # I want to get only bank and cash account
            ]
            debit = self.env['account.move.line'].read_group(domain, ['debit'], ['move_id']) # since it's cash received; get debit side only
            cash_received += sum(amount['debit'] for amount in debit)
            shipment.total_cash_received = cash_received

    def _get_revenue_invoice_and_remiburesed_invoice_ids(self):
        invoice_payment_info = {}
        invoice_payment_ids = []
        payment_account_move_ids = []
        all_invoice_ids = []

        domain = [ ('shipment_id', '=', self.id), ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('out_invoice', 'in_refund'))]
        cash_in_invoice_ids = self.env['account.move'].search(domain)

        if cash_in_invoice_ids:
            for inv_id in cash_in_invoice_ids:
                all_invoice_ids.append(inv_id)

        # loop to all invoices of shipment; Revenue Invoices and Remibursed Invoices
        for invoice_id in all_invoice_ids:
            invoice_payment_info = invoice_id._get_reconciled_info_JSON_values()
            for payment_vals in invoice_payment_info:
                payment_id = self.env['account.payment'].browse(payment_vals['account_payment_id'])
                invoice_payment_ids.append(payment_id)

        for payment_id in invoice_payment_ids:
            payment_account_move_ids.append(payment_id.move_id.id)

        return payment_account_move_ids

    def action_view_cash_received(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")
        account_move_ids = self._get_revenue_invoice_and_remiburesed_invoice_ids() or []
        action['domain'] = ["|", ('move_id', 'in', account_move_ids),
            ('move_id.shipment_id', '=', self.id),
            '&', ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ['entry']),
            ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id),
        ]
        return action

    def _total_invoices(self):
        for record in self:
            record.total_invoices = 0
            if not self.ids:
                return True
            domain = [
                ('shipment_id', '=', record.id),
                ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
            ]
            price_totals = self.env['account.move'].read_group(domain, ['amount_total_signed'], ['shipment_id'])
            record.total_invoices = sum(amount['amount_total_signed'] for amount in price_totals)

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('shipment_id', '=', self.id),
            ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
        ]
        if self.operation_type == 'import':
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'Import')], limit=1)
        elif self.operation_type == 'export':
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'Export')], limit=1)
        else:
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'Transit')], limit=1)
        action['context'] = {
            'default_move_type': 'out_invoice',
            'default_shipment_id': self.id,
            'default_partner_id': self.customer_id.id,
            'default_journal_id': journal_id.id,
        }
        return action
    # Total Revenue - Total Expense
    balance = fields.Monetary(currency_field='company_currency_id',compute='_operation_balance',
    groups='account.group_account_invoice,account.group_account_readonly')
    cash_balance = fields.Monetary(currency_field='company_currency_id',compute='_operation_balance',
    groups='account.group_account_invoice,account.group_account_readonly')

    tot_operation_expense = fields.Monetary(currency_field='company_currency_id',compute='compute_tot_operation_expense',
    groups='account.group_account_invoice,account.group_account_readonly', string="Total Expense",
            help="Get Total Expense Lines except Deposit&Rund Container amount at shipping line section"
                " and all reject status.")

    @api.onchange('total_invoices', 'total_expensed')
    def _operation_balance(self):
        for shipment in self:
            shipment.balance = shipment.total_invoices + shipment.tot_operation_expense
            shipment.cash_balance = shipment.total_cash_received + shipment.total_expensed

    @api.depends('tot_custom_permit_lines', 'tot_shipping_line_lines', 'tot_custom_duty_lines',
        'tot_clearance_lines', 'tot_port_charge_lines', 'tot_trucking_lines', 'tot_other_admin_lines')
    def compute_tot_operation_expense(self):
        for shipment in self:
            shipment.tot_operation_expense = - (
                shipment.tot_custom_permit_lines + shipment.tot_shipping_line_lines + \
                shipment.tot_custom_duty_lines + shipment.tot_clearance_lines + shipment.tot_port_charge_lines + \
                shipment.tot_trucking_lines + shipment.tot_other_admin_lines
            )

    #================= End Of Revenue and Expense Section =========================
    reimbursed_invoice_ids = fields.One2many(string='Reimbursed Invoices', inverse_name='shipment_id', comodel_name='account.move',
        domain=[('state', '=', 'posted'),('move_type', 'in', ('out_invoice', 'in_refund')), ('journal_id.is_reimbursement', '=', True)],
        readonly=True) # cash received
    reimbursed_bill_ids = fields.One2many(string='Reimbursed Bills', inverse_name='shipment_id', comodel_name='account.move',
        domain=[('state', '=', 'posted'),('move_type', 'in', ('out_refund', 'in_invoice',)), ('journal_id.is_reimbursement', '=', True)],
        readonly=True) # cash paid

    # Display at Processing Status
    @api.depends('reimbursed_invoice_ids.payment_state', 'reimbursed_bill_ids.payment_state', 'total_reimbursed_reciept', 'total_reimbursed_invoice')
    def _compute_reimbursement_date(self):
        for record in self:
            record.reimbursement_date = False
            domain = [ ('shipment_id', '=', record.id), ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')), ('journal_id.is_reimbursement', '=', True)]
            reimbursed_invoice_ids = self.env['account.move'].search(domain)
            for invoice in reimbursed_invoice_ids.sorted(lambda x: x.invoice_date or x.date):
                if (invoice.payment_state == "paid" or invoice.payment_state == "partial") and invoice.amount_total != 0.0:
                    invoice_payment_info = invoice._get_reconciled_info_JSON_values()
                    payment_id = 0
                    for payment_vals in invoice_payment_info:
                        payment_id = self.env['account.payment'].browse(payment_vals['account_payment_id'])
                    record.write({
                        "reimbursement_date": payment_id.date,
                    })
                else:
                    record.write({
                        "reimbursement_date": False,
                    })

    #================= Check Invoice of Shipment have payment or not ==============
    is_partially_paid = fields.Boolean(default=False,string="Partially Paid",readonly=1,copy=False, compute="_compute_invoice_state", compute_sudo=True, store=True)
    is_fully_paid = fields.Boolean(default=False,string="Fully Paid",readonly=1,copy=False, compute="_compute_invoice_state", compute_sudo=True, store=True)


    @api.depends('invoice_ids.payment_state', 'invoice_ids.state')
    def _received_payment_date(self):
        for record in self:
            record.issued_invoice_date = False
            record.received_payment_date = False
            for invoice in record.invoice_ids.sorted(lambda x: x.invoice_date):
                if invoice.invoice_date and invoice.state not in ['draft', 'cancel']:
                    record.write({
                        "issued_invoice_date": invoice.invoice_date,
                    })
                if (invoice.payment_state == "paid" or invoice.payment_state == "partial") and invoice.amount_total != 0.0:
                    invoice_payment_info = invoice._get_reconciled_info_JSON_values()
                    payment_id = 0
                    for payment_vals in invoice_payment_info:
                        payment_id = self.env['account.payment'].browse(payment_vals['account_payment_id'])
                    record.write({
                        "received_payment_date": payment_id.date,
                    })
                else:
                    record.write({
                        "received_payment_date": False,
                    })

    @api.depends('invoice_ids.payment_state')
    def _compute_invoice_state(self):
        for record in self:
            record.is_fully_paid = record.is_partially_paid = False
            for invoice in self.invoice_ids:
                if (invoice.payment_state == "paid" or invoice.payment_state == "partial"):
                    if invoice.payment_state == 'partial':
                        record.write({
                            "is_partially_paid": True,
                            "is_fully_paid": False,
                        })
                    amount = 0
                    if invoice.payment_state == 'paid' and invoice.amount_residual_signed == 0:
                        amount += invoice.amount_total_signed

                    if amount == invoice.amount_total_signed:
                        record.write({
                            "is_partially_paid": False,
                            "is_fully_paid": True,
                        })
                else:
                    record.write({
                        "is_fully_paid": False
                    })
    #================= END Check Invoice of Shipment have payment or not ================

    container_number1 = fields.Text(string="Container Number1", compute='get_container_lines', store=True)
    container_number2 = fields.Text(string="Container Number2", compute='get_container_lines', store=True)
    
    @api.depends('container_line_ids.container_number', 'container_line_ids.container_seal_number', 'num_of_truck', 'volume_cbm', 'shipment_type_id')
    def get_container_lines(self):
        for shipment in self:
            container_data = {}
            container_number = []
            seal_number = []
            for c in shipment.container_line_ids:
                if c.container_number:
                    c_number_type = c.container_number + '/' + c.container_type_id.code
                    container_number.append(c_number_type)
                if c.container_seal_number:
                    seal_number.append(c.container_seal_number)
                container_type = c.container_type_id.code
                if container_type in container_data:
                    # here just update the quantities of the same container
                    container_data[container_type] += 1
                else:
                    container_data[container_type] = 1

            shipment.container_number = "\n".join(container_number)
            # shipment.container_number =";".join(container_number)

        ###### Purpuse code below is to print frist 5 container number on the top and the rest is in the footer (18/Jan/2023)
            x = len(container_number) - 5
            if x > 0:
                shipment.container_number1 = "\n".join(container_number[:5])
                shipment.container_number2 = "\n".join(container_number[-x:])
            if x <= 0:
                shipment.container_number1 = "\n".join(container_number[:5])
                shipment.container_number2 = ""
        ######    

            shipment.seal_number = "\n ".join(seal_number)
            shipment.container_qty_type = "\n".join('{} x {}'.format(value, key) for key, value in container_data.items()) # Added this field on Mar 16 2022
            # If user input qty of truck, we want to display container qty type to | 1 x 40 = 3 Truck
            if shipment.num_of_truck != 0:
                if shipment.num_of_truck == 1: num_truck = " = " + str(shipment.num_of_truck) + " Truck"
                else: num_truck = " = " + str(shipment.num_of_truck) + " Trucks"
                shipment.container_qty_type += "".join(num_truck)
            if shipment.shipment_type_id.name == 'LCL':
                shipment.container_qty_type = shipment.volume_cbm
        return container_data

    @api.depends('truck_line_ids.truck_number', 'truck_line_ids.driver_number', 'truck_line_ids.container_id','container_line_ids.container_number')
    def get_trucking_lines(self):
        for shipment in self:
            driver_phone = []
            truck_container_info = {}
            if shipment.truck_line_ids:
                for truck in shipment.truck_line_ids:
                    truck_number = truck.truck_number
                    truck_container_info[truck_number] = truck.container_id.container_number
                    if truck.driver_number:
                        driver_phone.append(truck.driver_number)
                shipment.truck_container = "\n".join('{} / {}'.format(key, value) for key, value in truck_container_info.items())
                shipment.driver_phone = "\n".join(driver_phone)
            else:
                container_number=[]
                for container in shipment.container_line_ids:
                    if container.container_number:
                        container_number.append(container.container_number)    
                shipment.truck_container = "\n".join(container_number)

    @api.depends('truck_line_ids.delivery_location_id', 'truck_line_ids.loading_date',
        'truck_line_ids.release_empty_location_id', 'truck_line_ids.release_date', 'truck_line_ids.delivery_date')
    def get_trucking_info(self):
        for shipment in self:
            delivery_info = {}
            delivery_date = {}
            loading_unloading_info = {}
            dropoff_empty_info = {}
            dropoff_empty_date = {}
            for truck in shipment.truck_line_ids:
                delivery_loc = truck.delivery_location_id.name
                if delivery_loc in delivery_info:
                    # here just update the quantities of the same delivery location
                    delivery_info[delivery_loc] += 1
                else:
                    delivery_info[delivery_loc] = 1

                if truck.loading_date:
                    load_unload_date = truck.loading_date.strftime('%d/%b/%y')
                    if load_unload_date in loading_unloading_info:
                        # here just update the quantities of the same Loading/Unloading date
                        loading_unloading_info[load_unload_date] += 1
                    else:
                        loading_unloading_info[load_unload_date] = 1

                dropoff_loc = truck.release_empty_location_id.name
                if dropoff_loc in dropoff_empty_info:
                    # here just update the quantities of the same DropOff location
                    dropoff_empty_info[dropoff_loc] += 1
                else:
                    dropoff_empty_info[dropoff_loc] = 1

                if truck.release_date:
                    dropoff_date = truck.release_date.strftime('%d/%b/%y')
                    if dropoff_date in dropoff_empty_date:
                        # here just update the quantities of the same DropOff date
                        dropoff_empty_date[dropoff_date] += 1
                    else:
                        dropoff_empty_date[dropoff_date] = 1
                if truck.delivery_date:
                    date = truck.delivery_date.strftime('%d/%b/%y')
                    if date in delivery_date:
                        # here just update the quantities of the same delivery date
                        delivery_date[date] += 1
                    else:
                        delivery_date[date] = 1
            shipment.delivery_location = "\n".join('{}'.format(key) for key in delivery_info.keys())
            shipment.unloading_datetime = "\n".join('{}'.format(key) for key in loading_unloading_info.keys())
            shipment.empty_return_to = "\n".join('{}'.format(key) for key in dropoff_empty_info.keys())
            shipment.empty_return_date = "\n".join('{}'.format(key) for key in dropoff_empty_date.keys())
            shipment.delivery_date = "\n".join('{}'.format(key) for key in delivery_date.keys())

    def khmer_number(self, num):
        numInteger = num
        numString = str(numInteger)
        khmerNumber = ''
        numbersKhmer = ['០', '១', '២', '៣', '៤', '៥', '៦', '៧', '៨', '៩']
        i = 0
        for i in range(len(numString)):
            khmerNumber += numbersKhmer[int(numString[i])]
            i += 1
        return khmerNumber

    def khmer_month(self, num):
        khmerMonth = ''
        month = ['មករា', 'កុម្ភៈ', 'មីនា', 'មេសា', 'ឧសភា',
        'មិថុនា', 'កក្កដា', 'សីហា', 'កញ្ញា', 'តុលា', 'វិច្ឆិកា', 'ធ្នូ']
        khmerMonth = month[num]
        return khmerMonth

    def khmer_date_format(self):
        month = ['មករា', 'កុម្ភៈ', 'មីនា', 'មេសា', 'ឧសភា',
        'មិថុនា', 'កក្កដា', 'សីហា', 'កញ្ញា', 'តុលា', 'វិច្ឆិកា', 'ធ្នូ']
        khmerformattedDate = self.khmer_number(fields.Date.today().day)+ \
        ' ខែ ' + month[fields.Date.today().month - 1] + ' ឆ្នាំ ' + self.khmer_number(fields.Date.today().year)
        return khmerformattedDate

    def action_preview_import_documents(self):
        self.ensure_one()
        return {
            'name': 'Import Documents',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'devel_logistic_management.report_preview_import_document',
            'report_file': 'devel_logistic_management.report_preview_document',
            'res_model': 'operation.shipment',
        }

    def action_import_download_all(self):
        self.ensure_one()
        pdf_files = []
        if self.co_doc == True:
            co_form = self.env.ref('devel_logistic_management.dvl_co_form_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(co_form)
        if self.co_attactment_doc == True:
            co_attachment_doc = self.env.ref('devel_logistic_management.dvl_co_attachment_doc').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(co_attachment_doc)
        if self.inv_packing_doc == True:
            inv_packing_list = self.env.ref('devel_logistic_management.dvl_inv_packing_list_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(inv_packing_list)
        if self.transit_truck_bill_doc == True:
            transit_truck_bill_doc = self.env.ref('devel_logistic_management.dvl_transit_truck_bill_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(transit_truck_bill_doc)
        if self.authorization_doc == True:
            authorization_trader = self.env.ref('devel_logistic_management.dvl_authorization_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(authorization_trader)
        if self.transit_authorization_doc == True:
            authorization_broker = self.env.ref('devel_logistic_management.dvl_transit_authorization_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(authorization_broker)
        if self.permit_doc == True:
            permit_doc = self.env.ref('devel_logistic_management.dvl_permit_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(permit_doc)

        merge_pdf_files = pdf.merge_pdf(pdf_files)
        b64_merge_pdf = base64.b64encode(merge_pdf_files)
        name = self._get_report_base_filename()
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': name,
            'type': 'binary',
            'datas': b64_merge_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def action_preview_export_documents(self):
        self.ensure_one()
        return {
            'name': 'Export Documents',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'devel_logistic_management.report_preview_export_document',
            'report_file': 'devel_logistic_management.report_preview_document',
            'res_model': 'operation.shipment',
        }

    def action_export_download_all(self):
        self.ensure_one()
        # fixed pdf file under static/pdf/ folder
        file_path = get_module_resource('devel_logistic_management', 'static/pdf', 'export_inspection_form.pdf')
        fixed_file = open(file_path, 'rb').read()
        pdf_files = []
        if self.booking_order_doc == True:
            booking_order = self.env.ref('devel_logistic_management.dvl_booking_order_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(booking_order)
        if self.export_inv_packing_doc == True:
            export_inv_packing = self.env.ref('devel_logistic_management.dvl_export_inv_packing_list_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(export_inv_packing)
        if self.authorization_doc == True:
            authorization_trader = self.env.ref('devel_logistic_management.dvl_authorization_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(authorization_trader)
        if self.transit_authorization_doc == True:
            authorization_broker = self.env.ref('devel_logistic_management.dvl_transit_authorization_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(authorization_broker)
        if self.export_requirement_letter == True:
            export_requirement_letter = self.env.ref('devel_logistic_management.dvl_export_requirement_letter_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(export_requirement_letter)
        if self.guaranteed_letter == True:
            guaranteed_letter = self.env.ref('devel_logistic_management.dvl_export_guaranteed_letter_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(guaranteed_letter)
        if self.vgm == True:
            vgm = self.env.ref('devel_logistic_management.dvl_export_vgm_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(vgm)
        if self.draft_bl == True:
            draft_bl = self.env.ref('devel_logistic_management.dvl_export_draft_bl_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(draft_bl)
        if self.transit_truck_bill_doc == True:
            transit_truck_bill_doc = self.env.ref('devel_logistic_management.dvl_transit_truck_bill_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(transit_truck_bill_doc)
        if self.inspection_doc == True:
            inspection = self.env.ref('devel_logistic_management.dvl_export_inspection_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(inspection)
        if self.list_of_container == True:
            list_container = self.env.ref('devel_logistic_management.dvl_export_container_list').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(list_container)
        if self.inspection_fixed_doc == True:
            pdf_files.append(fixed_file)

        merge_pdf_files = pdf.merge_pdf(pdf_files)
        b64_merge_pdf = base64.b64encode(merge_pdf_files)
        name = self._get_report_base_filename()
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': name,
            'type': 'binary',
            'datas': b64_merge_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def action_preview_transit_documents(self):
        self.ensure_one()
        return {
            'name': 'Transit Documents',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'devel_logistic_management.report_preview_transit_document',
            'report_file': 'devel_logistic_management.report_preview_document',
            'res_model': 'operation.shipment',
        }

    def action_transit_download_all(self):
        self.ensure_one()
        pdf_files = []
        if self.transit_inv_packing_doc == True:
            transit_inv_packing_doc = self.env.ref('devel_logistic_management.dvl_transit_inv_packing_list_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(transit_inv_packing_doc)
        if self.draft_bl == True:
            draft_bl = self.env.ref('devel_logistic_management.dvl_export_draft_bl_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(draft_bl)
        if self.transit_truck_bill_doc == True:
            transit_truck_bill_doc = self.env.ref('devel_logistic_management.dvl_transit_truck_bill_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(transit_truck_bill_doc)
        if self.transit_authorization_doc == True:
            authorization_broker = self.env.ref('devel_logistic_management.dvl_transit_authorization_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(authorization_broker)
        if self.authorization_doc == True:
            authorization_trader = self.env.ref('devel_logistic_management.dvl_authorization_document').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(authorization_trader)

        merge_pdf_files = pdf.merge_pdf(pdf_files)
        b64_merge_pdf = base64.b64encode(merge_pdf_files)
        name = self._get_report_base_filename()
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': name,
            'type': 'binary',
            'datas': b64_merge_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def action_preview_accounting_documents(self):
        self.ensure_one()
        return {
            'name': 'Accounting Documents',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'devel_logistic_management.report_preview_accounting_document',
            'report_file': 'devel_logistic_management.report_preview_document',
            'res_model': 'operation.shipment',
        }

    def action_accounting_download_all(self):
        self.ensure_one()
        pdf_files = []
        if self.cover_file == True:
            cover_file = self.env.ref('devel_logistic_management.dvl_cover_file_shipment').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(cover_file)
        if self.cash_payment == True:
            cash_payment = self.env.ref('devel_logistic_management.dvl_cash_payment_request_shipment').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(cash_payment)
        if self.closing_file == True:
            closing_file = self.env.ref('devel_logistic_management.dvl_closing_file_shipment').sudo()._render_qweb_pdf(self.id)[0]
            pdf_files.append(closing_file)

        merge_pdf_files = pdf.merge_pdf(pdf_files)
        b64_merge_pdf = base64.b64encode(merge_pdf_files)
        name = self._get_report_base_filename()
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': name,
            'type': 'binary',
            'datas': b64_merge_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = '/web/content/' + str(attachment_id.id)
        return {
            'name': 'Report',
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def _get_report_base_filename(self):
        self.ensure_one()
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        date_today = pytz.utc.localize(datetime.datetime.today()).astimezone(user_tz)
        name = '%s_%s' % (self.name,date_today.strftime('%H:%M:%S'))
        return name

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') and vals.get('operation_type','import') == 'import':
            if vals.get('transportation_mode','sea') == 'sea':
                vals['name'] = self.env['ir.sequence'].next_by_code('operation.import') or _('New')
            elif vals.get('transportation_mode','air') == 'air':
                vals['name'] = self.env['ir.sequence'].next_by_code('operation.import.air') or _('New')
            elif vals.get('transportation_mode','road') == 'road':
                vals['name'] = self.env['ir.sequence'].next_by_code('operation.import.road') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('operation.import.other') or _('New')

        elif vals.get('name', _('New')) == _('New') and vals.get('operation_type','export') == 'export':
            vals['name'] = self.env['ir.sequence'].next_by_code('operation.export') or _('New')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('operation.transit') or _('New')

        result = super(OperationShipment, self).create(vals)
        return result

    def _get_name(self):
        record = self
        name = record.name or ''
        if self._context.get('show_commodity') and record.commodity:
            name = name + " - " + record.commodity
        if self._context.get('show_client_name') and record.customer_id:
            name = name + " - " + record.customer_id.name
        return name

    def name_get(self):
        res = []
        for record in self:
            name = record._get_name()
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", "|", ("name", operator, name), ("commodity", operator, name), ("customer_id.name", operator, name),]
        return self.search(domain, limit=limit).name_get()

    # If has CO Form Number, it get total_tax_amount_co else get total_tax_amount
    @api.depends('co_form_number', 'total_tax_amount', 'total_tax_amount_co')
    def _compute_total_estimated_tax_amount(self):
        for shipment in self:
            shipment.total_estimated_tax_amount = 0.0
            if shipment.co_form_number:
                shipment.total_estimated_tax_amount = shipment.total_tax_amount_co
            else:
                shipment.total_estimated_tax_amount = shipment.total_tax_amount


    # Compute Total Amount Invoice and Package List Qty
    @api.depends('line_ids.price_subtotal','line_ids.qty', 'line_ids.packing_list_qty', 'line_ids.net_weight',
        'line_ids.gross_weight', 'line_ids.tax_amount', 'line_ids.tax_amount_co')
    def _compute_sum_quantity(self):
        for shipment in self:
            shipment.total_amount = sum(shipment.mapped('line_ids.price_subtotal') or [0.0])
            shipment.total_qty = sum(shipment.mapped('line_ids.qty') or [0.0])
            shipment.total_pl_qty = sum(shipment.mapped('line_ids.packing_list_qty') or [0.0])
            shipment.total_net_weight = sum(shipment.mapped('line_ids.net_weight') or [0.0])
            shipment.total_gross_weight = sum(shipment.mapped('line_ids.gross_weight') or [0.0])
            shipment.total_tax_amount = sum(shipment.mapped('line_ids.tax_amount') or [0.0])
            shipment.total_tax_amount_co = sum(shipment.mapped('line_ids.tax_amount_co') or [0.0])

    ####Action export Invoice and Packing List Line In Customs Excel Format#####
    def export_inv_packing_line(self):
        self.ensure_one()
        return self.env.ref('devel_logistic_management.export_inv_packing_line_xlsx').report_action(self)

    #### Excel Template To Import Invoice and Packing List #####
    def _get_inv_pl_template(self):
        xls_path = get_module_resource('devel_logistic_management', 'static/excel', 'template_import_inv_pl.xlsx')
        self.inv_pl_template = base64.b64encode(open(xls_path, 'rb').read())

    inv_pl_template = fields.Binary(compute="_get_inv_pl_template")

    def action_read_operation_shipment(self):
        self.ensure_one()
        # I want to open the view in a new tab, if you can find a better way, please fix me!
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env.ref('devel_logistic_management.dvl_main_menu').id
        if self._context.get('processing_status_import'):
            action_id = self.env.ref("devel_logistic_management.action_operation_import_status").id
        elif self._context.get('processing_status_export'):
            action_id = self.env.ref("devel_logistic_management.action_operation_export_status").id
        elif self._context.get('deposit_container_report'):
            action_id = self.env.ref("devel_logistic_management.dvl_report_deposit_container_action").id
        else:
            action_id = self.env.ref("devel_logistic_management.action_dvl_operation_all").id
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': str(base_url) + "/web#id=%s&action=%s&model=operation.shipment&view_type=form&cids=%s&menu_id=%s" % (self.id, action_id, self.env.company.id, menu_id),
        }

    def action_view_operation_from_report(self):
        self.ensure_one()
        # I want to open the view in a new tab, if you can find a better way, please fix me!
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if self.operation_type == 'import':
            action_id = self.env.ref("devel_logistic_management.dvl_report_import_operation_action").id
        elif self.operation_type == 'export':
            action_id = self.env.ref("devel_logistic_management.dvl_report_export_operation_action").id
        elif self.operation_type == 'transit':
            action_id = self.env.ref("devel_logistic_management.dvl_report_transit_operation_action").id
        else:
            action_id = self.env.ref("devel_logistic_management.action_dvl_operation_all").id
        menu_id = self.env.ref('devel_logistic_management.dvl_main_menu').id
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': str(base_url) + "/web#id=%s&action=%s&model=operation.shipment&view_type=form&cids=%s&menu_id=%s" % (self.id, action_id, self.env.company.id, menu_id),
        }

    def get_date_range_from_Week(self):
        firstdayofweek = ''
        lastdayofweek = ''
        for record in self:
            base_date = fields.Date.from_string(record.date)
            firstdayofweek = base_date - datetime.timedelta(base_date.weekday())
            lastdayofweek = firstdayofweek + datetime.timedelta(days=6)
        return firstdayofweek, lastdayofweek

    def unlink(self):
        for shipment in self:
            raise UserError(_('You can not delete an operation shipment. Please archive it instead.'))
        return super(OperationShipment, self).unlink()

    @api.onchange('verify_user_id')
    def onchange_verify_user_id(self):
        for record in self:
            record.write({'to_review': False})

    def action_to_review(self):
        original_context = self.env.context
        body_template = self.env.ref('devel_logistic_management.shipment_review_assigned')
        if not self.verify_user_id:
            raise UserError(_('Please choose Review By Who!'))
        for record in self:
            model_description = self.env['ir.model']._get('operation.shipment').display_name
            body = body_template._render(
                dict(
                    record=record,
                    model_name ='operation.shipment',
                    res_id = record.id,
                    model_description=model_description,
                    access_link=self.env['mail.thread']._notify_get_action_link('view', model='operation.shipment', res_id=record.id),
                ),
                engine='ir.qweb',
                minimal_qcontext=True
            )
            if record.verify_user_id:
                record.message_notify(
                    partner_ids= record.verify_user_id.partner_id.ids,
                    body=body,
                    subject=_('%(record_name)s: %(user_name)s requested you to review this operation.',
                        record_name=record.name,
                        user_name= self.env.user.name),
                    record_name=record.name,
                    model_description=model_description,
                    email_layout_xmlid='mail.mail_notification_light',
                )
            body_template = body_template.with_context(original_context)
            self = self.with_context(original_context)
            record.write({'to_review': True})

    def create_attachments(self, attachment_ids=None, view_type='tree'):
        if attachment_ids is None:
            attachment_ids = []
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            raise UserError(_("No attachment was provided"))

        # can be use in multiple model like in other opertion service accounting attachments
        active_model = self._context.get('active_model')
        active_ids = self.env[active_model].browse(self._context.get('active_ids'))
        for attachment in attachments:
            attachment.write({
                'res_model': active_model,
                'res_id': active_ids.id,
                'accounting_document': True,
            })
            attachment.register_as_main_attachment()

    @api.depends('internal_note_lines')
    def _get_latest_internal_note_info(self):
        for shipment in self:
            timezone = self._context.get('tz')
            shipment.internal_note = shipment.internal_note or ''
            if shipment.internal_note_lines:
                latest_line = shipment.internal_note_lines.search([('shipment_id', '=', shipment.id)], limit=1 ,order='create_date desc')
                shipment.internal_note += latest_line.description or ''
                if latest_line.note_remark:
                    shipment.internal_note += ' || Remark: ' + latest_line.note_remark or ''
                shipment.internal_note += ' ( Record By: ' + str(latest_line.create_uid.name) or '' + ' '
                shipment.internal_note += ' ; ' + str(format_datetime(self.env, latest_line.create_date, timezone ,dt_format='d/MMM/yy HH:MM')) + ' )' or ''

    def _inverse_internal_note_info(self):
        pass

    @api.depends('cash_advance_line_ids.sub_total', 'cash_advance_line_ids.state')
    def _compute_total_cash_advance(self):
        for shipment in self:
            total_cash_advance = 0
            total_cash_advance_paid = 0
            shipment.total_cash_advance_amount = 0
            shipment.total_cash_advance_paid = 0
            for line in shipment.cash_advance_line_ids.filtered(lambda l: l.state not in ['reject']):
                total_cash_advance += line.sub_total
            for line in shipment.cash_advance_line_ids.filtered(lambda l: l.state in ['paid', 'direct_paid']):
                total_cash_advance_paid += line.sub_total
            shipment.total_cash_advance_amount = total_cash_advance
            shipment.total_cash_advance_paid = total_cash_advance_paid

    @api.depends('total_cash_advance_paid', 'total_cash_advance_cleared')
    def _compute_total_cash_advance_remaining(self):
        for shipment in self:
            shipment.total_cash_advance_remaining = shipment.total_cash_advance_paid - shipment.total_cash_advance_cleared

    @api.depends('expense_custom_permit_line_ids.clear_advance', 'expense_shipping_line_line_ids.clear_advance', 'expense_custom_duty_line_ids.clear_advance',
        'expense_clearance_line_ids.clear_advance', 'expense_port_charge_line_ids.clear_advance', 'expense_trucking_line_ids.clear_advance',
        'expense_other_admin_line_ids.clear_advance')
    def _compute_total_cash_advance_cleared(self):
        for shipment in self:
            total_cash_advance_cleared = 0
            shipment.total_cash_advance_cleared = 0
            for line in shipment.expense_custom_permit_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            for line in shipment.expense_shipping_line_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            for line in shipment.expense_custom_duty_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            for line in shipment.expense_clearance_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            for line in shipment.expense_port_charge_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            for line in shipment.expense_trucking_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            for line in shipment.expense_other_admin_line_ids.filtered(lambda  l: l.clear_advance == True):
                total_cash_advance_cleared += line.sub_total
            shipment.total_cash_advance_cleared = total_cash_advance_cleared

class OperationShipmentItem(models.Model):
    _name = "operation.shipment.item"
    _description = "Shipment Invoice & Packing List"

    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade', tracking=True)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
        related='shipment_id.company_currency_id')
    description = fields.Text(tracking=True)
    description_khmer = fields.Text(tracking=True)
    qty = fields.Float(tracking=True)
    uom_id = fields.Many2one('uom.unit')
    packing_list_qty = fields.Float(tracking=True)
    packing_list_uom_id = fields.Many2one('uom.unit')
    hs_code_id = fields.Many2one(comodel_name='hs.code', tracking=True, string="HS Code")
    remark_hs_code = fields.Char(string="Remark HS Code", tracking=True)
    fta = fields.Float(tracking=True)
    cd = fields.Char(related='hs_code_id.cd', tracking=True)
    st = fields.Char(related='hs_code_id.st', tracking=True)
    vat = fields.Char(related='hs_code_id.vat', tracking=True)
    price_unit = fields.Float(tracking=True, string="Unit Price")
    price_subtotal = fields.Float('Amount', compute='_compute_price_subtotal', tracking=True)
    price_subtotal_fob = fields.Float(tracking=True, string="FOB Amount")
    tax_amount = fields.Float(compute='_compute_tax_rate', inverse="_inverse_tax_rate", readonly=True,
        tracking=True, string="Tax Amount", help='Total Tax Amount before apply CO form')
    tax_amount_co = fields.Float(compute='_compute_tax_rate', inverse="_inverse_tax_rate", readonly=True,
        tracking=True, string="Tax Amount CO", help='Total Tax Amount after apply CO form')
    tax_rate = fields.Float(string="Tax Rate %", help='Total Tax Rate before apply CO form', readonly=True,
        inverse="_inverse_tax_rate", compute='_compute_tax_rate', store=True, tracking=True)
    tax_rate_co = fields.Float(string="Tax Rate CO %", help='Total Tax Rate after apply CO form', readonly=True,
        inverse="_inverse_tax_rate", compute='_compute_tax_rate', store=True, tracking=True)
    net_weight = fields.Float(tracking=True)
    gross_weight = fields.Float(tracking=True)
    new_tax_rate = fields.Char('New Tax Rate?',copy=False, tracking=True, help='New rate to re-calculate tax rate%')
    number = fields.Char(string="NBR In Book",help='The number in HS Code book.', tracking=True)
    number_in_co = fields.Char(string="NBR In CO",help='The number in CO', tracking=True)
    co_criteria = fields.Char(string="CO_Criteria", help='លក្ខខណ្ឌវិនិច្ឆ័យ', tracking=True)
    ministry_info = fields.Text(related='hs_code_id.ministry_info',string="Ministry", tracking=True)
    price_per_kg = fields.Float(tracking=True, string="Price Per KG", compute="_compute_price_per_kg")
    ###Extra Fields for INV and Packing List Lines that are vehicle
    is_vehicle = fields.Boolean(string="Is Vehicle?", related="shipment_id.is_vehicle")
    ###Extra Fields for INV and Packing List Lines that mix vehicle with othe commodity
    mix_commodity = fields.Boolean(string="Mix Commidity?", related="shipment_id.mix_commodity")
    v_type = fields.Many2one('vehicle.type', string="ប្រភេទយានយន្ត")
    new_used = fields.Selection(selection =[('new', 'NEW'),('used', 'USED')], string='ថ្មី ឬប្រើរួច', tracking=True)
    v_vin = fields.Char(string="លេខតួ")
    v_eng = fields.Char(string="លេខម៉ាស៊ីន") #Vehicle Engine| v_eng
    v_brand = fields.Many2one('vehicle.brand', string="ម៉ាក")
    v_model = fields.Char(string="ម៉ូដែល")
    v_power_mode = fields.Many2one('vehicle.power.mode', string="ប្រភេទថាមពលដែលប្រើប្រាស់")
    v_gvw = fields.Char(string="ទម្ងន់រថយន្តគិតទាំងបន្ទុក") #Gross Vehicle Weight| v_gvw
    v_model_year = fields.Char(string="ឆ្នាំម៉ូដែល")
    v_capacity = fields.Char(string="ទំហំស៊ីឡាំងគិតជា CC")
    v_left_hand_drive = fields.Selection(selection =[('left', 'LEFT-HAND-DRIVE'),('right', 'RIGHT-HAND-DRIVE')], string='ប្រភេទចង្កូត', tracking=True)
    v_other_info = fields.Char(string="ព័ត៌មានផ្សេងទៀតនៃយានយន្ត")
    wheel_type = fields.Selection(selection =[('4wd', '4WD'),('2wd', '2WD')], tracking=True)
    origin_country_id = fields.Many2one('res.country', string="Country of Origin", tracking=True)
    item_expiry_date = fields.Date(string="Expiry Date")
    item_manufacturing_date = fields.Date(string="Manufacturing Date")

    @api.depends('price_subtotal', 'gross_weight')
    def _compute_price_per_kg(self):
        for line in self:
            if line.gross_weight:
                line.price_per_kg = line.price_subtotal / line.gross_weight
            else:
                line.price_per_kg = 0

    @api.depends('price_unit', 'qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.qty

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    @api.depends('hs_code_id', 'hs_code_id.cd', 'hs_code_id.st', 'hs_code_id.vat',
                'hs_code_id.et', 'hs_code_id.at', 'fta', 'price_subtotal',
                'shipment_id.operation_type', 'new_tax_rate')
    @api.onchange('new_tax_rate')
    def _compute_tax_rate(self):
        for line in self:
            if line.shipment_id.operation_type == 'import':
                cd = float(line.hs_code_id.cd) / 100 # CD = Customs Tax
                st = float(line.hs_code_id.st) / 100 # ST = Special Tax
                vat = float(line.hs_code_id.vat) / 100 # VAT = Value Added Tax
                #et = float(line.hs_code_id.et) / 100 # ET = Export Tax
                at = float(line.hs_code_id.at) # AT = Additional Tax

                if line.new_tax_rate and float(line.new_tax_rate) == 0:
                    line.tax_rate_co = line.fta
                    line.tax_amount = 0
                    line.tax_amount_co = (line.price_subtotal * float(line.tax_rate_co)) / 100

                elif line.new_tax_rate and float(line.new_tax_rate) != 0 :
                    line.tax_rate_co = float(line.new_tax_rate) - (float(line.hs_code_id.cd) - line.fta)
                    line.tax_amount = (line.price_subtotal * float(line.new_tax_rate)) / 100
                    line.tax_amount_co = (line.price_subtotal * float(line.tax_rate_co)) / 100

                else:
                    line.tax_rate = ((1+cd)*(1+st)*(1+vat)-1) * 100
                    line.tax_rate_co = line.tax_rate - (float(line.hs_code_id.cd) - line.fta)
                    line.tax_amount = (line.price_subtotal*(1+cd)+(line.qty*at))*(1+st)*(1+vat) - line.price_subtotal
                    line.tax_amount_co = (line.price_subtotal*(1+cd)+(line.qty*at))*(1+st)*(1+vat) - line.price_subtotal * (1+(cd-(line.fta/100)))
            else:
                line.tax_rate = 0.0
                line.tax_rate_co = 0.0
                line.tax_amount = 0.0
                line.tax_amount_co = 0.0

    def _inverse_tax_rate(self):
        for line in self:
            if line.shipment_id.tax_calculation_id:
                for l in line.shipment_id.tax_calculation_id.line_ids:
                    line.tax_rate = l.tax_rate
                    line.tax_rate_co = l.tax_rate_co
                    line.tax_amount = l.tax_amount
                    line.tax_amount_co = l.tax_amount_co


class ShipmentContainer(models.Model):
    _name = "shipment.container"
    _description = "Shipment List of Containers"
    _rec_name = "container_number"
    _check_company_auto = True

    active = fields.Boolean('Active', related='shipment_id.active', tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', related='shipment_id.company_id', default=lambda self: self.env.company)
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade', tracking=True)
    container_type_id = fields.Many2one('container.type', tracking=True, required=True)
    custom_seal_no = fields.Char(string="Customs Seal N0.", tracking=True)
    container_number = fields.Char(tracking=True)
    container_seal_number = fields.Char(string="Seal N0.", tracking=True)
    company_seal_no = fields.Char(string="Company Seal N0.")
    package = fields.Many2one('uom.unit', tracking=True)
    weight = fields.Float(string='Empty Weight', tracking=True)
    gross_weight = fields.Float(string='Gross Weight', tracking=True)
    actual_gross_weight = fields.Float(string='Actual Gross Weight', tracking=True) # printed in VGM pdf actual GW
    volume = fields.Float(string='Volume(CBM)', tracking=True) # unused field - remove me if posible
    e_f = fields.Many2one('consignment', string="E/F", tracking=True)
    unit_price = fields.Float(tracking=True)

    transportation = fields.Char()
    remark = fields.Text()

    eta = fields.Date(string="ETA")
    return_date = fields.Date()
    takeout_date = fields.Date(string="ETR", help="ថ្ងៃយកចេញ")
    
    container_charge_type_id = fields.Many2one('storage.demurrage.charge', string="Container Charge Types")
    # number of days to charge
    number_storage_days = fields.Integer('#Days Storage',default=0)
    number_demurrage_days = fields.Integer('1st Demurrage',default=0)
    number_demurrage_days_1 = fields.Integer('2nd Demurrage', default=0)
    number_detention_days = fields.Integer('#Days Detention', default=0)
    number_penalty_days = fields.Integer('#Days Penalty', default=0)

    # list_container_num = fields.Char(string="Container Number")
    # @api.depends('')

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def _get_name(self):
        container = self
        name = container.container_number or ''
        if container.container_type_id:
            name += "/ %s" % (container.container_type_id.code)
        return name

    def name_get(self):
        res = []
        for container in self:
            name = container._get_name()
            res.append((container.id, name))
        return res


    @api.onchange('eta', 'takeout_date', 'container_charge_type_id.storage_day_free', 'storage_location')
    def _compute_storage_days(self):
        for line in self:
            if line.eta and line.takeout_date != False:
                if line.container_charge_type_id:
                    storage_days = line.takeout_date - line.eta
                    if line.container_charge_type_id.storage_location == "pp_location":
                        if storage_days.days + 1 <= line.container_charge_type_id.storage_day_free:
                            line.number_storage_days = 0
                        else:
                            line.number_storage_days = storage_days.days + 1 - line.container_charge_type_id.storage_day_free
                    else:
                        if storage_days.days + 1 <= line.container_charge_type_id.storage_day_free:
                            line.number_storage_days = 0
                        else:
                            line.number_storage_days = storage_days.days + 1
                else:
                    line.number_storage_days = 0

    # Compute 1st Demurrage charge 9 days
    @api.onchange('eta', 'takeout_date', 'container_charge_type_id.demurrage_9day_day_free')
    def _compute_demurrage_days(self):
        for line in self:
            if line.eta and line.takeout_date != False:
                if line.container_charge_type_id:
                    temp_demurrage_days = (line.takeout_date - line.eta).days + 1 - line.container_charge_type_id.demurrage_9day_day_free
                    if temp_demurrage_days <= 0:
                        demurrage_days = 0
                    else:
                        demurrage_days = temp_demurrage_days

                    if temp_demurrage_days <= line.container_charge_type_id.demurrage_9day_day_free:
                        line.number_demurrage_days = demurrage_days
                    else:
                        line.number_demurrage_days = line.container_charge_type_id.demurrage_9day_day_free
                else:
                    line.number_demurrage_days = 0

    # Compute 2nd Demurrage charge over 9 days
    @api.onchange('eta', 'takeout_date', 'number_demurrage_days',
                  'container_charge_type_id.demurrage_over_9day_day_free')
    def _compute_demurrage_days_1(self):
        for line in self:
            if line.eta and line.takeout_date != False:
                if line.container_charge_type_id:
                    temp_demurrage_days_1 = (line.takeout_date - line.eta).days - line.container_charge_type_id.demurrage_over_9day_day_free + 1
                    if temp_demurrage_days_1 <= 0:
                        demurrage_days = 0
                    else:
                        demurrage_days = temp_demurrage_days_1

                    demurrage_days1 = demurrage_days - line.number_demurrage_days

                    if temp_demurrage_days_1 <= line.container_charge_type_id.demurrage_over_9day_day_free:
                        line.number_demurrage_days_1 = 0
                    else:
                        line.number_demurrage_days_1 = demurrage_days1
                else:
                    line.number_demurrage_days_1 = 0
    @api.onchange('return_date', 'takeout_date', 'container_charge_type_id.detention_day_free')
    def _compute_detention_days(self):
        for line in self:
            if line.return_date and line.takeout_date != False:
                if line.container_charge_type_id:
                    detention_days = (line.return_date - line.takeout_date).days - line.container_charge_type_id.detention_day_free + 1
                    if detention_days <= 0:
                        line.number_detention_days = 0
                    else:
                        line.number_detention_days = detention_days
                else:
                    line.number_detention_days = 0

    @api.onchange('eta', 'takeout_date', 'container_charge_type_id.customs_penalty_day_free')
    def _compute_penalty_days(self):
        for line in self:
            if line.eta and line.takeout_date != False:
                if line.container_charge_type_id:
                    penalty_day = (line.takeout_date - line.eta).days - line.container_charge_type_id.customs_penalty_day_free + 1
                    if penalty_day <= 0:
                        line.number_penalty_days = 0
                    else:
                        line.number_penalty_days = penalty_day
                else:
                    line.number_penalty_days = 0

    # Amount to charge in USD
    storage_charge = fields.Monetary(readonly=True,currency_field='currency_id',
        compute="_compute_storage_charge")
    demurrage_charge = fields.Monetary(readonly=True,currency_field='currency_id',
        compute="_compute_demurrage_charge")
    detention_charge = fields.Monetary(readonly=True,currency_field='currency_id', compute="_compute_detention_charge")
    custom_penalty_charge = fields.Monetary(readonly=True,currency_field='currency_id',
        compute="_custom_penalty_charge")
    total_charge = fields.Monetary(readonly=True,currency_field='currency_id',
        compute="_total_charge")

    currency_id = fields.Many2one('res.currency', string='Currency', related='shipment_id.company_id.currency_id')

    @api.depends('number_storage_days', 'container_charge_type_id.storage_price')
    def _compute_storage_charge(self):
        for line in self:
            line.storage_charge = line.number_storage_days * line.container_charge_type_id.storage_price

    @api.depends('number_demurrage_days', 'number_demurrage_days_1',
    'container_charge_type_id.demurrage_9day_price', 'container_charge_type_id.demurrage_over_9day_price')
    def _compute_demurrage_charge(self):
        for line in self:
            line.demurrage_charge = (line.number_demurrage_days * line.container_charge_type_id.demurrage_9day_price) + (line.number_demurrage_days_1 * line.container_charge_type_id.demurrage_over_9day_price)

    @api.depends('number_detention_days', 'container_charge_type_id.detention_price')
    def _compute_detention_charge(self):
        for line in self:
            line.detention_charge = line.number_detention_days * line.container_charge_type_id.detention_price

    @api.depends('number_penalty_days', 'shipment_id.customs_penalty_price')
    def _custom_penalty_charge(self):
        for line in self:
            line.custom_penalty_charge = line.number_penalty_days * line.shipment_id.customs_penalty_price

    def _total_charge(self):
        for line in self:
            line.total_charge = line.storage_charge + line.demurrage_charge + line.detention_charge + line.custom_penalty_charge

    #This field is for Trucking line
    #But will calulates it in this model
    number_standby_days = fields.Integer('#Days Standby', default=0)

    @api.onchange('return_date', 'takeout_date', 'container_charge_type_id.standby_day_free')
    def _compute_standby_days(self):
        for line in self:
            if line.return_date and line.takeout_date != False:
                if line.container_charge_type_id:
                    standby_day = (line.return_date - line.takeout_date).days - line.container_charge_type_id.standby_day_free
                    if standby_day <= 0:
                        line.number_standby_days = 0
                    else:
                        line.number_standby_days = standby_day
                else:
                    line.number_standby_days = 0

    standby_charge = fields.Monetary(readonly=True, currency_field='currency_id',compute="_compute_standby_charge")

    @api.depends('number_standby_days', 'container_charge_type_id.standby_price')
    def _compute_standby_charge(self):
        for line in self:
            line.standby_charge = line.number_standby_days * line.container_charge_type_id.standby_price

    storage_charge_date = fields.Date()
    demurrage_charge_date = fields.Date()

    @api.onchange('eta', 'container_type_id.charge_type_id.storage_day_free', 'container_charge_type_id.demurrage_9day_day_free')
    def _compute_storage_demrrage_charge_date(self):
        for line in self:
            if line.container_charge_type_id:
                if line.eta != False:
                    storage_charge_date = line.container_charge_type_id.storage_day_free
                    demurrage_charge_date = line.container_charge_type_id.demurrage_9day_day_free
                    line.storage_charge_date = line.eta + timedelta(days=storage_charge_date)
                    line.demurrage_charge_date = line.eta + timedelta(days=demurrage_charge_date)


class ShipmentInternalNote(models.Model):
    _name = "shipment.internal.note"
    _description = "List of Shipment Internal Notes"
    _order = "create_date desc, id desc"

    shipment_id = fields.Many2one('operation.shipment')
    description = fields.Text(tracking=True, string="Description Notes")
    note_remark = fields.Text(tracking=True, string="Remark")

class OperationCashAdvance(models.Model):
    _name = "operation.cash.advance"
    _description = "Manage Shipment Operation Cash Advance"
    _check_company_auto = True

    @api.returns('self')
    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    shipment_id = fields.Many2one('operation.shipment')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', related='shipment_id.company_id', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string="Currency", default=_get_default_currency_id)
    request_date = fields.Datetime(string="Request Date", tracking=True, copy=False, default=lambda self: fields.Datetime.now())
    requester_user_id = fields.Many2one('res.users', string='Requested By', compute_sudo=True, store=True, readonly=True,
                     domain=[('active', '=', True)], copy=False)
    account_id = fields.Many2one('account.account', string='Account', index=True, ondelete="cascade", check_company=True, tracking=True,
            domain="[('company_id', '=', company_id), ('deprecated', '=', False), ('is_off_balance', '=', False), ('internal_type', '=', 'other')]")
    description = fields.Text(tracking=True)
    qty = fields.Float(default=1.0, string="QTY")
    unit_price = fields.Float()
    sub_total = fields.Monetary(string="Sub Total",currency_field='currency_id', compute="_compute_subtotal_amount",
                    groups='account.group_account_invoice,account.group_account_readonly')
    approver_user_id = fields.Many2one('res.users', string='Approved By', compute_sudo=True, store=True, readonly=True, copy=False,
        domain=[('active', '=', True)])
    approved_date = fields.Datetime(tracking=True, copy=False)
    advance_date = fields.Datetime(string="Advance Date")
    advance_user_id = fields.Many2one('res.users', string='Advanced By', compute_sudo=True, store=True, readonly=True,
                    domain=[('active', '=', True)], copy=False)
    received_user_id = fields.Many2one('res.partner', string='Received By', compute_sudo=True, store=True, copy=False,
        domain=[('active', '=', True)])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),],
        string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,)
    move_id = fields.Many2one('account.move', copy=False)

    @api.depends('qty', 'unit_price', 'currency_id')
    def _compute_subtotal_amount(self):
        for line in self:
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.request_date) * line.qty

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this advance!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Advance Line must be in draft status in order to approve.'))

        self.filtered(lambda request: request.state == 'draft').write({'state': 'validate', 'approver_user_id': self.env.user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be in draft status in order to reject it'))
        self.filtered(lambda request: request.state == 'draft').write({'state': 'reject'})
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'advance_user_id': False,
            'advance_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink()
        })
        return True

    @api.model
    def default_get(self, fields):
        res = super(OperationCashAdvance, self).default_get(fields)
        # It seems to be a bug in native odoo that the field partner_id or other many2one
        # fields are not in the fields list by default. A workaround is required
        # to force this. So
        if "default_shipment_id" in self._context and "shipment_id" not in fields:
            fields.append("shipment_id")
            res["shipment_id"] = self._context.get("default_shipment_id")

        if "default_requester_user_id" in self._context and "requester_user_id" not in fields:
            fields.append("requester_user_id")
            res["requester_user_id"] = self._context.get("default_requester_user_id")
        return res

    def _check_line_unlink(self):
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not delete line that already Approved or Advanced!'))
        return super(OperationCashAdvance, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)
