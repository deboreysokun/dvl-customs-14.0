odoo.define('devel_logistic_management.documents.upload.mixin', function (require) {
    "use strict";

    var core = require('web.core');
    var config = require('web.config');
    var _t = core._t;
    var qweb = core.qweb;

    /**
    * Mixin for uploading single or multiple documents.
    */
    var DvlDocumentUploadMixin = {
        start: function () {
            // define a unique uploadId and a callback method
            this.fileUploadID = _.uniqueId('dvl_document_upload');
            $(window).on(this.fileUploadID, this._onFileUploaded.bind(this));
            return this._super.apply(this, arguments);
        },
        /**
         * @private
         */
        _onAddAttachment: function (ev) {
            // Auto submit form once we've selected an attachment
            var $input = $(ev.currentTarget).find('input.o_input_file');
            if ($input.val() !== '') {
                var $binaryForm = this.$('.o_dvl_documents_upload form.o_form_binary_form');
                $binaryForm.submit();
            }
        },
        /**
         * @private
         */
        _onFileUploaded: function () {
            // Callback once attachment have been created, create an expense with attachment ids
            var self = this;
            var attachments = Array.prototype.slice.call(arguments, 1);
            // Get id from result
            var attachent_ids = attachments.reduce(function (filtered, record) {
                if (record.id) {
                    filtered.push(record.id);
                }
                return filtered;
            }, []);
            if (!attachent_ids.length) {
                return self.do_notify(false, _t("An error occurred during the upload"));
            }
            var myContext = this.initialState.context
            myContext['isMobile'] = config.device.isMobile
            return this._rpc({
                model: 'operation.shipment',
                method: 'create_attachments',
                args: ["", attachent_ids, this.viewType],
                context: myContext,
            }).then(function (result) {
                self.trigger_up('reload');
            });
        },
        /**
         * @private
         * @param {Event} event
         */
        _onUpload: function (event) {
            var self = this;
            // If hidden upload form don't exists, create it
            var $formContainer = this.$('.o_content').find('.o_dvl_documents_upload');
            if (!$formContainer.length) {
                $formContainer = $(qweb.render('dvl.DocumentsHiddenUploadForm', { widget: this }));
                $formContainer.appendTo(this.$('.o_content'));
            }
            // Trigger the input to select a file
            this.$('.o_dvl_documents_upload .o_input_file').click();
        },
    };

    return DvlDocumentUploadMixin;

});
