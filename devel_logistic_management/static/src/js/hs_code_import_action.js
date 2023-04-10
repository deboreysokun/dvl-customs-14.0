odoo.define('devel_logistic_management.hs_code_import_action', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.BasicModel');
    var DataImport = require('base_import.import');
    var Dialog = require('web.Dialog');

    DataImport.DataImport.include({

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this._target = action.target;
            this._dialog_height = action.params.height || '1000px';
            this.show_required = action.params.show_required || false;
            this.import_field = action.params.import_field || false;
            this.action_id = action.jsID;


        },
        need_import: function () {
            return this._target == 'new' && this.import_field;
        },
        exit: function () {
            if (!this.need_import()) {
                return this._super.apply(this, arguments);
            }
            if (this.action_manager.currentDialogController) {
                //If the action is in the dialog, close the dialog
                this.action_manager.currentDialogController.dialog.close();
            }

        },
        import_options: function () {
            var options = this._super.apply(this, arguments);
            var is_import = this.need_import();
            if (options && is_import) {
                var controller = this.getController();
                var model = controller.model;
                var line = model.get(controller.handle);
                _.extend(options, {
                    import_hscode_item: is_import,
                    import_field: line.fields[this.import_field].relation_field,
                    year_id: line.data['name'],
                });
            }
            return options;
        },
        getController: function () {
            //Get form controller
            return this.action_manager.getCurrentController().widget;
        },

        renderButtons: function (footer) {
            this._super.apply(this, arguments);
            if (footer && this.need_import()) {
                var controller = this.action_manager.currentDialogController;
                if (controller && controller.dialog) {
                    //Set the height of the dialog
                    controller.dialog.$el.css("height", this._dialog_height);
                    controller.dialog.$el.find('.oe_import').css('position', 'relative');
                    controller.dialog.$el.find('.o_control_panel').hide()
                    footer.append(this.$buttons);
                }
            }
        },
    });
});
