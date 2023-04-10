odoo.define('devel_logistic_management.form_widgets', function (require) {
    "use strict";

    var BasicController = require('web.BasicController');
    var core = require('web.core');
    var utils = require('web.utils');
    var _t = core._t;
    var Dialog = require('web.Dialog');
    var fieldRegistry = require('web.field_registry');
    var ListRenderer = require('web.ListRenderer');
    var rpc = require('web.rpc');
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;

    BasicController.include({
        /**
        * Called each time the controller is dettached into the DOM
        * Override this method to remove resetLocalState() (DVL requirement)
        * to keep current position, scrollbar, active tab..etc
        * @override
        */
        on_detach_callback() {
        },
    });

    ListRenderer.include({
        /**
         * Override this method to give a specific empty row in list view (DVL requirement)
         * Default Odoo will render at least 4 rows in List view.
         * You can also set a empty_rows attribute in the tree tag to define the number of empty rows
         * <tree string="" editable="bottom" empty_rows="4">
        */
        _renderBody: function () {
            var self = this;
            var $body = $('<tbody>');
            var empty_rows = 0;
            if (self.arch && self.arch.attrs.empty_rows) {
                empty_rows = self.arch.attrs.empty_rows;
            }
            var $rows = this._renderRows();
            while ($rows.length < empty_rows) {
                $rows.push(this._renderEmptyRow());
            }
            $body.append($rows);

            // handle reordering lines in list view
            if (this.hasHandle) {
                $body.sortable({
                    axis: 'y',
                    items: '> tr.o_data_row',
                    helper: 'clone',
                    handle: '.o_row_handle',
                    stop: function (event, ui) {
                        // update currentID taking moved line into account
                        if (self.currentRow !== null) {
                            var currentID = self.state.data[self.currentRow].id;
                            self.currentRow = self._getRow(currentID).index();
                        }
                        self.unselectRow().then(function () {
                            self._moveRecord(ui.item.data('id'), ui.item.index());
                        });
                    },
                });
            }
            return $body;
        },
        // Override this method to get button appear,disappear logic
        _updateSelection: function () {
            this.selection = [];
            var self = this;
            var $inputs = this.$('tbody .o_list_record_selector input:visible:not(:disabled)');
            var allChecked = $inputs.length > 0;
            var model;
            $inputs.each(function (index, input) {
                if (input.checked) {
                    self.selection.push($(input).closest('tr').data('id'));
                    $(input).closest('tr').addClass("o_data_row_selected"); // set background color for selected row
                } else {
                    allChecked = false;
                    $(input).closest('tr').removeClass("o_data_row_selected");
                }
            });
            utils.traverse_records(this.state, function (record) {
                if (_.contains(self.selection, record.id)) {
                    model = record.model // find selected records model
                }
            });
            if (this.selection.length > 0 && model === 'shipment.expense.customs.office.permit') {
                $('.button_confirm_expense_lines_cop').show()
                $('.button_approve_expense_lines_cop').show()
                $('.btn_confirm_approve_expense_line_cop').show()
                $('.button_draft_expense_lines_cop').show()
                $('.button_pay_expense_lines_cop').show()
                $('.button_set_received_by_cop').show()
                $('.button_reimbursement_cop').show()
                $('.button_direct_pay_cop').show()
                $('.btn_clear_cash_advance_cop').show()
            }
            else if (this.selection.length > 0 && model === 'shipment.expense.shipping.line') {
                $('.button_confirm_expense_lines_spl').show()
                $('.button_approve_expense_lines_spl').show()
                $('.btn_confirm_approve_expense_line_spl').show()
                $('.button_draft_expense_lines_spl').show()
                $('.button_pay_expense_lines_spl').show()
                $('.button_set_received_by_spl').show()
                $('.button_reimbursement_spl').show()
                $('.button_direct_pay_spl').show()
                $('.btn_clear_cash_advance_spl').show()
            }
            else if (this.selection.length > 0 && model === 'shipment.expense.clearance') {
                $('.button_confirm_expense_lines_cle').show()
                $('.button_approve_expense_lines_cle').show()
                $('.btn_confirm_approve_expense_line_cle').show()
                $('.button_draft_expense_lines_cle').show()
                $('.button_pay_expense_lines_cle').show()
                $('.button_set_received_by_cle').show()
                $('.button_reimbursement_cle').show()
                $('.button_direct_pay_cle').show()
                $('.btn_clear_cash_advance_cle').show()
            }
            else if (this.selection.length > 0 && model === 'shipment.expense.custom.duty') {
                $('.button_confirm_expense_lines_cdt').show()
                $('.button_approve_expense_lines_cdt').show()
                $('.btn_confirm_approve_expense_line_cdt').show()
                $('.button_draft_expense_lines_cdt').show()
                $('.button_pay_expense_lines_cdt').show()
                $('.button_set_received_by_cdt').show()
                $('.button_reimbursement_cdt').show()
                $('.button_direct_pay_cdt').show()
                $('.btn_clear_cash_advance_cdt').show()
            }
            else if (this.selection.length > 0 && model === 'shipment.expense.port.charge') {
                $('.button_confirm_expense_lines_ptg').show()
                $('.button_approve_expense_lines_ptg').show()
                $('.btn_confirm_approve_expense_line_ptg').show()
                $('.button_draft_expense_lines_ptg').show()
                $('.button_pay_expense_lines_ptg').show()
                $('.button_set_received_by_ptg').show()
                $('.button_reimbursement_ptg').show()
                $('.button_direct_pay_ptg').show()
                $('.btn_clear_cash_advance_ptg').show()
            }
            else if (this.selection.length > 0 && model === 'shipment.expense.trucking') {
                $('.button_confirm_expense_lines_tk').show()
                $('.button_approve_expense_lines_tk').show()
                $('.btn_confirm_approve_expense_line_tk').show()
                $('.button_draft_expense_lines_tk').show()
                $('.button_pay_expense_lines_tk').show()
                $('.button_set_received_by_tk').show()
                $('.button_reimbursement_tk').show()
                $('.button_direct_pay_tk').show()
                $('.btn_clear_cash_advance_tk').show()
            }
            else if (this.selection.length > 0 && model === 'shipment.expense.other.admin') {
                $('.button_confirm_expense_lines_otd').show()
                $('.button_approve_expense_lines_otd').show()
                $('.btn_confirm_approve_expense_line_otd').show()
                $('.button_draft_expense_lines_otd').show()
                $('.button_pay_expense_lines_otd').show()
                $('.button_set_received_by_otd').show()
                $('.button_reimbursement_otd').show()
                $('.button_direct_pay_otd').show()
                $('.btn_clear_cash_advance_otd').show()
            }
            else if (this.selection.length > 0 && model === 'other.operation.expense.line') {
                $('.button_confirm_expense_lines').show()
                $('.button_approve_expense_lines').show()
                $('.btn_confirm_approve_expense_line').show()
                $('.button_draft_expense_lines').show()
                // button in other.operation | other service type
                $('.btn_pay_other_expense_line').show()
                $('.btn_direct_pay_other_expense_line').show()
            }
            else if (this.selection.length > 0 && model === 'operation.cash.advance') {
                $('.btn_cash_advance_payment').show()
            }
            else {
                // Button above operation.cash.advance
                $('.btn_cash_advance_payment').hide()

                // Button above shipment.expense.customs.office.permit  model
                $('.button_confirm_expense_lines_cop').hide()
                $('.button_approve_expense_lines_cop').hide()
                $('.btn_confirm_approve_expense_line_cop').hide()
                $('.button_draft_expense_lines_cop').hide()
                $('.button_pay_expense_lines_cop').hide()
                $('.button_set_received_by_cop').hide()
                $('.button_reimbursement_cop').hide()
                $('.button_direct_pay_cop').hide()
                $('.btn_clear_cash_advance_cop').hide()

                // Button above shipment.expense.shipping.line model
                $('.button_confirm_expense_lines_spl').hide()
                $('.button_approve_expense_lines_spl').hide()
                $('.btn_confirm_approve_expense_line_spl').hide()
                $('.button_draft_expense_lines_spl').hide()
                $('.button_pay_expense_lines_spl').hide()
                $('.button_set_received_by_spl').hide()
                $('.button_reimbursement_spl').hide()
                $('.button_direct_pay_spl').hide()
                $('.btn_clear_cash_advance_spl').hide()

                // Button above shipment.expense.clearance model
                $('.button_confirm_expense_lines_cle').hide()
                $('.button_approve_expense_lines_cle').hide()
                $('.btn_confirm_approve_expense_line_cle').hide()
                $('.button_draft_expense_lines_cle').hide()
                $('.button_pay_expense_lines_cle').hide()
                $('.button_set_received_by_cle').hide()
                $('.button_reimbursement_cle').hide()
                $('.button_direct_pay_cle').hide()
                $('.btn_clear_cash_advance_cle').hide()

                // Button above shipment.expense.custom.duty model
                $('.button_confirm_expense_lines_cdt').hide()
                $('.button_approve_expense_lines_cdt').hide()
                $('.btn_confirm_approve_expense_line_cdt').hide()
                $('.button_draft_expense_lines_cdt').hide()
                $('.button_pay_expense_lines_cdt').hide()
                $('.button_set_received_by_cdt').hide()
                $('.button_reimbursement_cdt').hide()
                $('.button_direct_pay_cdt').hide()
                $('.btn_clear_cash_advance_cdt').hide()

                // Button above shipment.expense.port.charge model
                $('.button_confirm_expense_lines_ptg').hide()
                $('.button_approve_expense_lines_ptg').hide()
                $('.btn_confirm_approve_expense_line_ptg').hide()
                $('.button_draft_expense_lines_ptg').hide()
                $('.button_pay_expense_lines_ptg').hide()
                $('.button_set_received_by_ptg').hide()
                $('.button_reimbursement_ptg').hide()
                $('.button_direct_pay_ptg').hide()
                $('.btn_clear_cash_advance_ptg').hide()

                // Button above shipment.expense.trucking model
                $('.button_confirm_expense_lines_tk').hide()
                $('.button_approve_expense_lines_tk').hide()
                $('.btn_confirm_approve_expense_line_tk').hide()
                $('.button_draft_expense_lines_tk').hide()
                $('.button_pay_expense_lines_tk').hide()
                $('.button_set_received_by_tk').hide()
                $('.button_reimbursement_tk').hide()
                $('.button_direct_pay_tk').hide()
                $('.btn_clear_cash_advance_tk').hide()

                // Button above shipment.expense.other.admin model
                $('.button_confirm_expense_lines_otd').hide()
                $('.button_approve_expense_lines_otd').hide()
                $('.btn_confirm_approve_expense_line_otd').hide()
                $('.button_draft_expense_lines_otd').hide()
                $('.button_pay_expense_lines_otd').hide()
                $('.button_set_received_by_otd').hide()
                $('.button_reimbursement_otd').hide()
                $('.button_direct_pay_otd').hide()
                $('.btn_clear_cash_advance_otd').hide()

                // button in other.operation | other service type
                // button in other operation service expense line
                $('.button_confirm_expense_lines').hide()
                $('.button_approve_expense_lines').hide()
                $('.btn_confirm_approve_expense_line').hide()
                $('.button_draft_expense_lines').hide()
                $('.button_set_received_by').hide()
                $('.btn_pay_other_expense_line').hide()
                $('.btn_direct_pay_other_expense_line').hide()
            }
            this.$('thead .o_list_record_selector input').prop('checked', allChecked);
            this.trigger_up('selection_changed', { selection: this.selection });
            this._updateFooter();
        },
    });
    // For Other Operation Services
    var One2ManySelectable = FieldOne2Many.extend({
        template: 'One2ManySelectable',
        events: {
            "click .button_confirm_expense_lines": "action_confirm_lines",
            "click .button_approve_expense_lines": "action_approve_lines",
            "click .btn_confirm_approve_expense_line": "action_confirm_approve_lines",
            "click .button_draft_expense_lines": "_confirmResetRecordToDraft",
            "click .button_set_received_by": "action_set_received_by",
            "click .btn_pay_other_expense_line": "action_pay_lines_other_operation",
            "click .btn_direct_pay_other_expense_line": "action_direct_payment_other_service",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_pay_lines_other_operation: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_other_operation.view_other_operation_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'other.operation.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment_other_service: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_other_operation.view_other_operation_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'other.operation.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('one2many_selectable', One2ManySelectable);

    var SelectableCustomsOfficePermit = FieldOne2Many.extend({
        template: 'SelectableCustomsOfficePermit',
        events: {
            // button above  customs.office.permit model // short name cop
            "click .button_confirm_expense_lines_cop": "action_confirm_lines",
            "click .button_approve_expense_lines_cop": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_cop": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_cop": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_cop": "action_pay_lines",
            "click .button_set_received_by_cop": "action_set_received_by",
            "click .button_reimbursement_cop": "action_reimbursement_expense_line",
            "click .button_direct_pay_cop": "action_direct_payment",

            "click .btn_clear_cash_advance_cop": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_customs_office_permit', SelectableCustomsOfficePermit);

    var SelectableShippingLine = FieldOne2Many.extend({
        template: 'SelectableShippingLine',
        events: {
            // button above shipping line model // short name spl
            "click .button_confirm_expense_lines_spl": "action_confirm_lines",
            "click .button_approve_expense_lines_spl": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_spl": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_spl": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_spl": "action_pay_lines",
            "click .button_set_received_by_spl": "action_set_received_by",
            "click .button_reimbursement_spl": "action_reimbursement_expense_line",
            "click .button_direct_pay_spl": "action_direct_payment",

            "click .btn_clear_cash_advance_spl": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },


        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_shipping_line', SelectableShippingLine);

    var SelectableClearance = FieldOne2Many.extend({
        template: 'SelectableClearance',
        events: {
            // button above clearance model // short name cle
            "click .button_confirm_expense_lines_cle": "action_confirm_lines",
            "click .button_approve_expense_lines_cle": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_cle": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_cle": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_cle": "action_pay_lines",
            "click .button_set_received_by_cle": "action_set_received_by",
            "click .button_reimbursement_cle": "action_reimbursement_expense_line",
            "click .button_direct_pay_cle": "action_direct_payment",

            "click .btn_clear_cash_advance_cle": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_clearance', SelectableClearance);

    var SelectableCustomDuty = FieldOne2Many.extend({
        template: 'SelectableCustomDuty',
        events: {
            // button above shipping line model // short name cdt
            "click .button_confirm_expense_lines_cdt": "action_confirm_lines",
            "click .button_approve_expense_lines_cdt": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_cdt": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_cdt": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_cdt": "action_pay_lines",
            "click .button_set_received_by_cdt": "action_set_received_by",
            "click .button_reimbursement_cdt": "action_reimbursement_expense_line",
            "click .button_direct_pay_cdt": "action_direct_payment",

            "click .btn_clear_cash_advance_cdt": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_custom_duty', SelectableCustomDuty);

    var SelectablePortCharge = FieldOne2Many.extend({
        template: 'SelectablePortCharge',
        events: {
            // button above shipping line model / short name ptg
            "click .button_confirm_expense_lines_ptg": "action_confirm_lines",
            "click .button_approve_expense_lines_ptg": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_ptg": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_ptg": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_ptg": "action_pay_lines",
            "click .button_set_received_by_ptg": "action_set_received_by",
            "click .button_reimbursement_ptg": "action_reimbursement_expense_line",
            "click .button_direct_pay_ptg": "action_direct_payment",

            "click .btn_clear_cash_advance_ptg": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_port_charge', SelectablePortCharge);

    var SelectableTrucking = FieldOne2Many.extend({
        template: 'SelectableTrucking',
        events: {
            // button above shipping line model // short name tk
            "click .button_confirm_expense_lines_tk": "action_confirm_lines",
            "click .button_approve_expense_lines_tk": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_tk": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_tk": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_tk": "action_pay_lines",
            "click .button_set_received_by_tk": "action_set_received_by",
            "click .button_reimbursement_tk": "action_reimbursement_expense_line",
            "click .button_direct_pay_tk": "action_direct_payment",

            "click .btn_clear_cash_advance_tk": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_trucking', SelectableTrucking);

    var SelectableOtherAdmin = FieldOne2Many.extend({
        template: 'SelectableOtherAdmin',
        events: {
            // button above shipping line model / short name otd
            "click .button_confirm_expense_lines_otd": "action_confirm_lines",
            "click .button_approve_expense_lines_otd": "action_approve_lines",
            "click .btn_confirm_approve_expense_line_otd": "action_confirm_approve_lines",
            "click .button_draft_expense_lines_otd": "_confirmResetRecordToDraft",
            "click .button_pay_expense_lines_otd": "action_pay_lines",
            "click .button_set_received_by_otd": "action_set_received_by",
            "click .button_reimbursement_otd": "action_reimbursement_expense_line",
            "click .button_direct_pay_otd": "action_direct_payment",

            "click .btn_clear_cash_advance_otd": "action_clear_cash_advance",
        },

        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        _confirmResetRecordToDraft: async function () {
            Dialog.confirm(
                this,
                _t("Are you sure that you want to reset to draft?"),
                {
                    confirm_callback: () => this.action_draft_lines(),
                }
            );
        },
        // Action for Logistic Operation | model: 'operation.shipment'
        action_confirm_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'approve_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Approved", "Refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_confirm_approve_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'confirm_and_approve',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_notify("Successfully Confirmed", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_draft_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            rpc.query({
                'model': 'operation.shipment',
                'method': 'draft_expense_lines',
                'args': [selected_ids, model],
            }).then(function (result) {
                //self.do_warn("Successfully Reset To Draft", "Do more Action! Or refresh the page to see the change!");
                self.trigger_up('reload', { keepChanges: false });
            });
        },
        action_pay_lines: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_set_received_by: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_set_received_by_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Update Recevied By Who',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        action_reimbursement_expense_line: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_reimburse_lines_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Generate Reimbursement Invoice',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.reimbursement',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_direct_payment: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_lines_direct_payment'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Direct Payment',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },
        action_clear_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_expense_clear_cash_advance'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Clear Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'expense.line.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_other_admin', SelectableOtherAdmin);

    var SelectableCashAdvance = FieldOne2Many.extend({
        template: 'SelectableCashAdvance',
        events: {
            "click .btn_cash_advance_payment": "action_pay_cash_advance",
        },
        start: function () {
            this._super.apply(this, arguments);
            var self = this;
        },

        action_pay_cash_advance: function () {
            var self = this;
            var selected_ids = self.get_selected_ids_one2many();
            var model = self.get_selected_mode_one2many();
            if (selected_ids.length === 0) {
                this.do_warn(_t("You must choose at least one record."));
                return false;
            }
            self._rpc({
                // Get view id
                model:'ir.model.data',
                method:'xmlid_to_res_model_res_id',
                args: ['devel_logistic_management.view_advance_payment_form'], // View id goes here
            }).then(function(data){
                // Open view
                self.do_action({
                        name: 'Register Cash Advance',
                        type: 'ir.actions.act_window',
                        res_model: 'cash.advance.payment',
                        context: {
                            'active_model': model,
                            'active_ids': selected_ids,
                        },
                        target: 'new',
                        views: [[data[1], 'form']], // data[1] variable contains the view id
                    },{on_close: function () {
                        self.trigger_up('reload', { keepChanges: true });
                    }
                });
            });
        },

        //////////////////////////////////////////////////////////////
        _getRenderer: function () {
            if (this.view.arch.tag === 'kanban') {
                return One2ManyKanbanRenderer;
            }
            if (this.view.arch.tag === 'tree') {
                return ListRenderer.extend({
                    init: function (parent, state, params) {
                        this._super.apply(this, arguments);
                        this.hasSelectors = true;
                    },
                });
            }
            return this._super.apply(this, arguments);
        },
        //collecting the selected IDS from one2manay list
        get_selected_ids_one2many: function () {
            var self = this;
            var ids = [];
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    ids.push(parseInt(self._getResId($(this).data('id'))));
                });
            return ids;
        },
        _getResId: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.res_id;
        },
        get_selected_mode_one2many: function () {
            var self = this;
            var model;
            this.$el.find('td.o_list_record_selector input:checked')
                .closest('tr').each(function () {
                    model = self._getModel($(this).data('id'));
                });
            return model;
        },
        _getModel: function (recordId) {
            var record;
            var model;
            utils.traverse_records(this.recordData[this.name], function (r) {
                if (r.id === recordId) {
                    record = r;
                }
            });
            return record.model;
        },

    });
    fieldRegistry.add('selectable_cash_advance_payment', SelectableCashAdvance);

    return {
        One2ManySelectable: One2ManySelectable,
        SelectableCustomsOfficePermit: SelectableCustomsOfficePermit,
        SelectableShippingLine: SelectableShippingLine,
        SelectableClearance: SelectableClearance,
        SelectableCustomDuty: SelectableCustomDuty,
        SelectablePortCharge: SelectablePortCharge,
        SelectableTrucking: SelectableTrucking,
        SelectableOtherAdmin: SelectableOtherAdmin,
        SelectableCashAdvance: SelectableCashAdvance,
    };
});
