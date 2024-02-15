from odoo import models

class ExpenseSummaryXlsx(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_expense_summary_xlsx'
    inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        
        workbook.default_format_properties = {'font_name': 'Times New Roman', 'font_size': 12}
        worksheet = workbook.add_worksheet('Expense Summary')
        
        # Set Column Width
        
        worksheet.set_column('A:A', 10) # No.
        worksheet.set_column('B:B', 32) # Request Date
        worksheet.set_column('C:C', 32) # Shipment Referance
        worksheet.set_column('D:D', 25) # Type
        worksheet.set_column('E:E', 22) # Expense Category
        worksheet.set_column('F:F', 20) # BL Number
        worksheet.set_column('G:G', 20) # Container Number
        worksheet.set_column('H:H', 20) # Commodity
        worksheet.set_column('I:I', 20) # ETA
        worksheet.set_column('J:J', 25) # Original Amount
        worksheet.set_column('K:K', 25) # Balance

        # Set Column Styling

        main_header = workbook.add_format({'bold': True, 'border': 0, 'valign': 'vcenter', 'align': 'center', 'font_size': 20, 'font_name': 'Arial'})

        sub_header = workbook.add_format({'bold': True, 'border': 2, 'valign': 'vcenter', 'align': 'center', 'font_size': 16, 'font_name': 'Arial'})

        text_format = workbook.add_format({'border': 1,'valign': 'vcenter', 'align': 'center', 'font_size': 12, 'font_name': 'Arial'})

        number_format = workbook.add_format({'num_format': '$#,##0'})

        # Set Headers
        
        worksheet.merge_range('A1:K2', 'DEVEL LOGISTICS CO., LTD\nSUMMARY REPORT\nPay To  : "(contact)"', main_header)
        worksheet.write('A3', 'No.', sub_header)
        worksheet.write('B3', 'Request Date', sub_header)
        worksheet.write('C3', 'Shipment Referance', sub_header)
        worksheet.write('D3', 'Type', sub_header)
        worksheet.write('E3', 'Expense Category', sub_header)
        worksheet.write('F3', 'BL Number', sub_header)
        worksheet.write('G3', 'Container No.', sub_header)
        worksheet.write('H3', 'Commodity', sub_header)
        worksheet.write('I3', 'ETA', sub_header)
        worksheet.write('J3', 'Original Amount', sub_header)
        worksheet.write('K3', 'Balance', sub_header)

        # Get Data

        shipment_reference = data["shipment_reference"]
        type = data["type"]
        total_amounts = data["total_amounts"]
        balance = 0

        # Insert Data

        starting_row = 4
        number = 1

        for category, amount in total_amounts.items():
            balance += amount
            worksheet.write(f"A{starting_row}", number, text_format)
            worksheet.write(f"B{starting_row}", "", text_format)
            worksheet.write(f"C{starting_row}", shipment_reference, text_format)
            worksheet.write(f"D{starting_row}", type, text_format)
            worksheet.write(f"E{starting_row}", category, text_format)
            worksheet.write(f"F{starting_row}","", text_format)
            worksheet.write(f"G{starting_row}", "", text_format)
            worksheet.write(f"H{starting_row}", "",text_format)
            worksheet.write(f"I{starting_row}", "", text_format)
            worksheet.write(f"J{starting_row}", amount, number_format)
            worksheet.write(f"K{starting_row}", balance, number_format)
            number += 1

        
        # Bank Information
        worksheet.merge_range(f"A{starting_row + 1}:C{starting_row + 1}", "Bank Information", worksheet.add_format({'underline': True, 'bold': True,'border': 1,'valign': 'vcenter', 'align': 'center', 'font_size': 12, 'font_name': 'Arial'}))