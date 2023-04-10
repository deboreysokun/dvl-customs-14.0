## Module <devel_logistic_management>

#### 08.11.2021
#### Version 14.0.1.0.0
#### ADD
- Initial commit for Devel Logistic Management

#### 15.11.2021
#### Version 14.0.1.1.1
#### UPDT
- Fixed error
- Adjustment File Name and added storage.demurrage

#### 25.11.2021
#### Version 14.0.1.2.2
#### UPDT
- Added permit document
- adjustment tax_calulation

#### 30.11.2021
#### Version 14.0.1.3.3
#### UPDT
- Added persoanl information to res.partner
- adjustment contaner deposit function


#### 06.12.2021
#### Version 14.0.1.3.4
#### UPDT
- Field parameter tracking and added requirement letter

#### 09.12.2021
#### Version 14.0.2.4.4
#### UPDT
- Modification on HS CODE model
- Added Calendar View  and Processing Status

#### 24.12.2021
#### Version 14.0.2.5.5
#### UPDT
- Tiny Adjustment
- Added contact menuitem
- Added Expense Line payment process workflow

#### 27.12.2021
#### Version 14.0.2.6.5
#### UPDT
- Added Sales Quotation
- Updated Access Rule

#### 31.12.2021
#### Version 14.0.2.7.6
#### UPDT
- Added Transit Document


#### 17.01.2022
#### Version 14.0.2.7.7
#### UPDT
- Added reset to draft feature on expense lines

#### 19.01.2022
#### Version 14.0.2.8.8
#### UPDT
- Export Docs, List of Container, and 2 inspection docs added

#### 20.01.2022
#### Version 14.0.2.9.9
#### UPDT
- Truck Bill added


#### 21.01.2022
#### Version 14.0.2.10.9
#### UPDT
- Added new authroization form

#### 24.01.2022
#### Version 14.0.2.10.10
#### UPDT
- Adjustment authorization form

#### 26.01.2022
#### Version 14.0.3.11.11
#### UPDT
- Remove storage.demurrage model
- Added total_thc_amount; total_duty_tax_amount
- Added is_truck on res.partner; adjustment truck booking

#### 27.01.2022
#### Version 14.0.3.11.12
#### UPDT
- Remove tracking attr, hide expense line button from normal user

#### 28.01.2022
#### Version 14.0.3.12.13
#### UPDT
- Added Preview Import, Export, Transit, and Closing File Shipment Documents
- Fixed closing file shipment - Revenue Table (wrong tr)

#### 01.02.2022
#### Version 14.0.3.13.13
#### UPDT
- Added new fields for tax calculation model to recalculate tax rate & amount
- Added UOM field for Package List

#### 03.02.2022
#### Version 14.0.3.14.13
#### UPDT
- Updated processing status menu: linked trucking info
- Change sequence Import operation

#### 05.02.2022
#### Version 14.0.3.15.14
#### UPDT
- Added Check Tax status confirm workflow; Check Tax line form view added.
- Fixed warning message on tracking fields
- Replace report tag with record tag in debit note invoice, tax invoice, and sale quotation

#### 09.02.2022
#### Version 14.0.3.16.14
#### UPDT
- Updated Operation View Form and Processing status list view

#### 11.02.2022
#### Version 14.0.3.17.15
#### UPDT
- Added reject status on expense line, total operation balance
- Fixed vgm and requirement letter
- Added get date range from week
- Update qweb reports

#### 14.02.2022
#### Version 14.0.3.18.16
#### UPDT
- Remove class tariff_center for operation expense line
- Added 'draft all' server action to expense lines
- add new style sheet to list view

#### 15.02.2022
#### Version 14.0.3.19.16
#### UPDT
- Added sum to inv and packing line items
- Added shipment ref to account invoice and journal entry list view

#### 17.02.2022
#### Version 14.0.4.21.17
#### UPDT
- Added confirm,approve,draft all in operation expense line; new widget 'one2many_selectable' added
- Adjustment stylesheet of List View
- Adjustment on tax calculation
- Update authorization form and add new field customs_emp_id
- Added bussiness activities field to res.partner, update guarantee letter

#### 18.02.2022
#### Version 14.0.4.22.18
#### UPDT
- reload page on expense after confirm, approve
- improve operation filter search
- Added confirm_approve button on expense lines
- customer and supplier aging feature in accounting, and move_type field to list view
- Added sample='1' to tree view

#### 19.02.2022
#### Version 14.0.4.23.19
#### UPDT
- fixed access error on custome&supplier aging
- adjustment style
- Added packing list qty

#### 21.02.2022
#### Version 14.0.4.25.20
#### UPDT
- added computed tax amount in operation shipment
- Added Filter To Confirm, To Approve, To Pay in Operation Shipment
- Added remark_hs_code field on check tax, and alignment text center
- Fixed bugs on total_invoices, total_expensed, total_cash_received
- UPDT Report Menu Item and added Transit Report

#### 22.02.2022
#### Version 14.0.4.26.21
#### UPDT
- Show Customs Duty Expense line for all Shipment Type
- Computed Total Amount in Expense Line Payment Wizard View
- Expenese Line compute requested Date

#### 23.02.2022
#### Version 14.0.4.27.21
#### UPDT
- Set disable_autofocus to false in form view
- Added button linked to shipment form in Report Meun

#### 24.02.2022
#### Version 14.0.4.28.21
#### UPDT
- Apply pay button in expense lines, Remove action button expense line in header
- Apply decoration in operation list view, move documnet page to information page
- Added new field price_per_kg, company_currency_id in invoice and PL list, updated processing status menu css

#### 25.02.2022
#### Version 14.0.4.29.21
#### UPDT
- Remove render at least 4 rows in List view
- Add company_header_id, update tax invoice and debit note invoice

#### 26.02.2022
#### Version 14.0.4.30.21
#### UPDT
- Hide accounting info and data from operation user

#### 27.02.2022
#### Version 14.0.4.30.22
#### UPDT
- Adjustment on container deposit, expense line payment
- Added incoterm to inv and packing list

#### 28.02.2022
#### Version 14.0.4.31.23
#### UPDT
- Adjustment stylesheet
- UPDT inv incoterm on inv and packing list
- FIXED cannot reordering lines in list view

#### 01.03.2022
#### Version 14.0.4.32.23
#### UPDT
- Added feature add tax amount to expense line
- Adjustment on truck booking view

#### 02.03.2022
#### Version 14.0.4.33.23
#### UPDT
- Adde request to review feature
- Show button and tax amount in expense lines tab

#### 04.03.2022
#### Version 14.0.4.34.23
#### UPDT
- Overwrite JS basic controller - Remove resetLocalState() form on_detach_callback()

#### 06.03.2022
#### Version 14.0.4.35.23
#### UPDT
- IMP - HS Code Year

#### 11.03.2022
#### Version 14.0.4.36.23
#### UPDT
- Add Provice List; Add widget show partner bank info at expense line received by field.

#### 13.03.2022
#### Version 14.0.4.36.24
#### UPDT
- Fixed Wrong Khmer Month

#### 14.03.2022
#### Version 14.0.4.37.24
#### UPDT
- Add new feture export "INV and PL" in customs (follow គយ import format) format

#### 16.03.2022
#### Version 14.0.4.38.24
#### UPDT
- Add additional fields to INV and PL model for vehicle hs code; vehicle type, vehicle brand, and vehicle power mode model added.

#### 18.03.2022
#### Version 14.0.4.39.24
#### UPDT
- Add Reimbursement Receipt in Operation Shipment
- Separate action attachment for Operation work and Accounting Work.

#### 21.03.2022
#### Version 14.0.4.40.24
#### UPDT
- Added new "Upload" button at attachment listview and kanban view.
- Added attachment_category app

#### 22.03.2022
#### Version 14.0.4.41.24
#### UPDT
- UPDAT format INV and PL of type Vehicle, expiry and mauf. date

#### 24.03.2022
#### Version 14.0.4.42.24
#### UPDT
- Fixed DVL Sale quotation line order sequence

#### 29.03.2022
#### Version 14.0.4.43.24
#### UPDT
- Added preview and quotation template on DVL sales quotation

#### 30.03.2022
#### Version 14.0.4.44.24
#### UPDT
- Add new import fuction to INV and PL
- Adjustment on sales quotation

#### 01.04.2022
#### Version 14.0.4.45.24
#### UPDT
- Add defualt download template to import INV and PL
- Copy from function on Operation Shipment model

#### 05.04.2022
#### Version 14.0.4.46.25
#### UPDT
- Added nbr_in_co field in INV and PL
- Added sequence handle line; paid status reset to draft; and change date fields to datetime fields on Expesen line model.
- Modify feature import and export INV and PL lines.
- IMP expense line reject action reason

#### 19.04.2022
#### Version 14.0.4.47.26
#### UPDT
- Add Document print with or without stamp and signature
- Add Currency, rates on expense line.

#### 20.04.2022
#### Version 14.0.4.48.27
#### UPDT
- Modify method "action_read_operation_shipment" to open in a new tab instead of current window.
- Fixed few bugs on feature import and export INV and PL

#### 21.04.2022
#### Version 14.0.4.49.27
#### UPDT
- Exclued Deposit and Reund container amount from total shipment operation expense amount

#### 25.04.2022
#### Version 14.0.4.50.27
#### UPDT
- ADD Reimbursement Feature in Operation Shipment

#### 27.04.2022
#### Version 14.0.4.51.27
#### UPDT
- Overwrite _get_name of Partner model to show mobile and phone on contact form

#### 03.05.2022
#### Version 14.0.4.52.27
#### UPDT
- Add copy from shipment expense line
- Adjustment reimbursement feature
- Add sequence field to _order on account.move.line
- Overwirte onchange uom_id to remove recompute unit price on account.move.line

#### 04.05.2022
#### Version 14.0.4.53.27
#### UPDT
- Add Offical receipt pdf to invoices pdf when invoices are paid or have payment.

#### 09.05.2022
#### Version 14.0.4.54.28
#### UPDT
- Fixed expense line with negative unit price amount
- Added new action "Create bankslip" on account.move
- Added new paper format "Less Header A4"

#### 11.05.2022
#### Version 14.0.4.55.28
#### UPDT
- Update INV and PL to handle with Commodity mixed item. eg: Vehical, expriy item,..etc

#### 13.05.2022
#### Version 14.0.4.56.28
#### UPDT
- Added new field "number of turck". If have number of truck, don't show container number in INV and PL pdf
- Adjust style in expense line view

#### 17.05.2022
#### Version 14.0.4.57.28
#### UPDT
- Added FOB amount, Co Criteria to inv and pl line

#### 18.05.2022
#### Version 14.0.4.57.29
#### UPDT
- Fixed error on v_capacity field

#### 23.05.2022
#### Version 14.0.4.58.29
#### UPDT
- Added Partner Invoice Payment History

#### 26.05.2022
#### Version 14.0.4.59.30
#### UPDT
- Fix bug on container_number get seal_number
- Adjust Operation List View style

#### 31.05.2022
#### Version 14.0.4.60.31
#### UPDT
- Fixed some tiny bug
- Adde new state and action for direct payment in expense line

#### 01.06.2022
#### Version 14.0.4.61.31
#### UPDT
- Added internal note field and apply readonly when shipment move to done stage

#### 03.06.2022
#### Version 14.0.4.62.31
#### UPDT
- Separate action confirm, validate approve...ect. for all expense line sections.

#### 07.06.2022
#### Version 14.0.4.63.31
#### UPDT
- Added action reimbursment in and out

#### 08.06.2022
#### Version 14.0.4.64.31
#### UPDT
- Modify shipment refund container to handle multiple refund

#### 15.06.2022
#### Version 14.0.4.65.32
#### UPDT
- Fixed wrong calulation error for reimbursement invocie
- Added freeze column in Report menu
- Change color style on decorations

#### 16.06.2022
#### Version 14.0.4.66.32
#### UPDT
- Added copy form in account.move

#### 17.06.2022
#### Version 14.0.4.67.33
#### UPDT
- Improve loading time in Deposit Container Report due to computed field

#### 20.06.2022
#### Version 14.0.4.68.33
#### UPDT
- Added action "create quotation from quotation template"

#### 21.06.2022
#### Version 14.0.4.69.33
#### UPDT
- Remove computed method from expense line requested date field.
- Adjustment on stylesheet
- Show action "Create quotation template" in form view

#### 23.06.2022
#### Version 14.0.4.70.33
#### UPDT
- Link action view journal items on cash received and cash paid fields.

#### 27.06.2022
#### Version 14.0.4.71.34
#### UPDT
- Added custom decoration
- Added new methon to compute shipment's invoice fully paid or partial paid.

#### 28.06.2022
#### Version 14.0.4.72.34
#### UPDT
- Overwrite onchange product id method on account.move
- Adjust stylesheel file

#### 30.06.2022
#### Version 14.0.4.73.35
#### UPDT
- Add more existign port fiels to list view
- Restrict delete direct_paid status in expense line

#### 06.07.2022
#### Version 14.0.4.74.35
#### UPDT
- Add direct paid status amount to total amount field of each section in expense line.
- Adjust operation closing file shipment pdf

#### 07.07.2022
#### Version 14.0.4.75.35
#### UPDT
- Added 2 decimal digit to qty in all invoice pdf
- Inclued draft bl and truck bill to export and transit operation download action.
- Allow 5 charater for incoterm code
- Added new total estimatd tax; if have co form id get co tax amount, else get tax amount.
- Added base_name_search_improved oca app

#### 11.07.2022
#### Version 14.0.5.76.35
#### UPDT
- Migration field type location from char to many2one fields
- Add container_id in trucking expense line
- Remove freeze columns in mobile phone

#### 12.07.2022
#### Version 14.0.5.77.35
#### UPDT
- Added internal note lines
- Adjustment container_qty_type to get volume_cbm instead when shipment type is LCL
- Added extra fields of POL and POD at Carrier section.

#### 13.07.2022
#### Version 14.0.5.78.35
#### UPDT
- Adjust format datetime of internal note field, and add it to kanban view.

#### 15.07.2022
#### Version 14.0.5.79.35
#### UPDT
- Adjust INV and PL export feature to get FTA rate even if it is 0.

#### 18.07.2022
#### Version 14.0.5.80.35
#### UPDT
- Added Cash Advance and Clearing management

#### 19.07.2022
#### Version 14.0.5.81.36
#### UPDT
- Fixed bugs in cash advance
- Added option "print only receipt for paid invoice"

#### 21.07.2022
#### Version 14.0.5.82.36
#### UPDT
- Added Cover File and Cash Request Payment template
- Hide Option "Print only receipt for paid invoice" in Journal Entry.

#### 22.07.2022
#### Version 14.0.5.83.36
#### UPDT
- Adjust Quarantee letter, Inspection letter, and new format of authorization for export operation.

#### 26.07.2022
#### Version 14.0.5.83.37
#### UPDT
- Fixed bug in INV and PL and expense line requested date

#### 27.07.2022
#### Version 14.0.5.84.38
#### UPDT
- linked each report header to right action when open in new tab
- Get default journal in account.move based on operation type.
