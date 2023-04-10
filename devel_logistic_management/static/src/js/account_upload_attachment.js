odoo.define('devel_logistic_management.account.documents.upload', function (require) {
    "use strict";
    var DvlDocumentUploadMixin = require('devel_logistic_management.documents.upload.mixin');
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var core = require('web.core');

    var QWeb = core.qweb;

    var DvlListController = ListController.extend(DvlDocumentUploadMixin, {
        buttons_template: 'DvlDocumentListView.buttons',
        events: _.extend({}, ListController.prototype.events, {
            'click .o_button_upload_dvl_document': '_onUpload',
            'change .o_dvl_documents_upload .o_form_binary_form': '_onAddAttachment',
        }),
    });

    var DvlListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: DvlListController,
        }),
    });

    var DvlKanbanController = KanbanController.extend(DvlDocumentUploadMixin, {
        buttons_template: 'DvlDocumentKanbanView.buttons',
        events: _.extend({}, KanbanController.prototype.events, {
            'click .o_button_upload_dvl_document': '_onUpload',
            'change .o_dvl_documents_upload .o_form_binary_form': '_onAddAttachment',
        }),
    });

    // The kanban view
    var DvlDocumentsKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: DvlKanbanController,
        }),
    });

    viewRegistry.add('dvl_document_list', DvlListView);
    viewRegistry.add('dvl_document_kanban', DvlDocumentsKanbanView);

});
