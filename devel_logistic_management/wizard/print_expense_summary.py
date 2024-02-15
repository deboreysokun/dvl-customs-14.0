from odoo import models, api, fields


class PrintExpenseSummary(models.TransientModel):
    _name = 'print.expense.summary'

    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime(required=True)

    name = fields.Char(string='Report Name', required=True, default=lambda self: self._default_name(), read_only=True)

    def _default_name(self):
        current_partner = self.env['res.partner'].browse(self.env.context.get('active_id'))
        return current_partner.name

    def print_expense_summary(self):

        current_partner = self.env['res.partner'].browse(self.env.context.get('active_id'))

        import_domain = [('operation_type', '=', 'import')]
        export_domain = [('operation_type', '=', 'export')]
        transit_domain = [('operation_type', '=', 'transit')]

        import_operations = self.env['operation.shipment'].search(import_domain)
        export_operations = self.env['operation.shipment'].search(export_domain)
        transit_operations = self.env['operation.shipment'].search(transit_domain)
        all_operations = self.env["operation.shipment"].search([])

        data = {
            "Import": [],
            "Export": [],
            "Transit": [],
            "Other": [],
        }

        def get_data(operations):

            result = []

            for operation in operations:

                operation_data = {
                    "shipment_reference": operation.name,
                    "type": operation.operation_type,
                    "bl_number": f"{operation.bl_number}+{operation.truck_bill_number if operation.truck_bill_number else ''}",
                    "container_no": operation.truck_container,
                    "commodity": operation.commodity,
                    "eta": operation.eta,
                    "expense_lines": [],
                }

                

                # Customs Valuation Office
                if operation.expense_custom_permit_line_ids:
                    for line in operation.expense_custom_permit_line_ids:
                        expense_line = {
                            "category": "Customs Valuation Office",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }

                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                # Shipping Line
                if operation.expense_shipping_line_line_ids:
                    for line in operation.expense_shipping_line_line_ids:
                        expense_line = {
                            "category": "Shipping Line",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }
                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                # Customs Duty
                if operation.expense_custom_duty_line_ids:
                    for line in operation.expense_custom_duty_line_ids:
                        expense_line = {
                            "category": "Customs Duty",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }

                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                # Clearance
                if operation.expense_clearance_line_ids:
                    for line in operation.expense_clearance_line_ids:
                        expense_line = {
                            "category": "Clearance",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }

                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                # Port Charge
                if operation.expense_port_charge_line_ids:
                    for line in operation.expense_port_charge_line_ids:
                        expense_line = {
                            "category": "Port Charge",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }

                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                # Trucking
                if operation.expense_trucking_line_ids:
                    for line in operation.expense_trucking_line_ids:
                        expense_line = {
                            "category": "Trucking",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }

                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                # Other Admin Expenses
                if operation.expense_other_admin_line_ids:
                    for line in operation.expense_other_admin_line_ids:
                        expense_line = {
                            "category": "Other Admin Expenses",
                            "sub_total": line.sub_total,
                            "received_by": line.received_user_id.name,
                            "state": line.state,
                            "requested_date": line.requested_date
                        }

                        if self.start_date <= expense_line["requested_date"] <= self.end_date and expense_line["state"] == "confirm" and expense_line["received_by"] == current_partner.name:
                            operation_data["expense_lines"].append(expense_line)

                result.append(operation_data)

            return result
            
        data["Import"] = get_data(import_operations)
        data["Export"] = get_data(export_operations)
        data["Transit"] = get_data(transit_operations)

        

        report_data = {
            "contact": current_partner.name,
            "lines": []
        }

        all_operations = data["Import"] + data["Export"] + data["Transit"]

        filter = []

        for operation in all_operations:   

            if len(operation['expense_lines']) > 0:
                
                for expense_line in operation['expense_lines']:

                    total_amounts = {
                        "Customs Valuation Office": 0,
                        "Shipping Line": 0,
                        "Customs Duty": 0,
                        "Clearance": 0,
                        "Port Charge": 0,
                        "Trucking": 0,
                        "Other Admin Expenses": 0,
                    }

                    total_amounts[expense_line["category"]] += expense_line["sub_total"]

                    line = {
                        "request_date": expense_line["requested_date"].date(),
                        "shipment_reference" : operation["shipment_reference"],
                        "type" : operation["type"],
                        "bl_number": operation["bl_number"],
                        "container_no": operation["container_no"],
                        "commodity": operation["commodity"],
                        "eta": operation["eta"],
                        "total_amounts": total_amounts
                    }

                    report_data["lines"].append(line)

        print("=" * 10)

        print("Report Data Lines:", report_data["lines"])

        return self.env.ref('devel_logistic_management.action_expense_summary').with_context(landscape=True).report_action(None, data=report_data)
