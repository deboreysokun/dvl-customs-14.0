odoo.define('devel_logistic_managment.bankinfo', function (require) {
"use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var QWeb = core.qweb;

    var ShowBankInfoWidget = AbstractField.extend({
        _render: function() {
            var self = this;
            var info = JSON.parse(this.value);
            if (!info) {
                this.$el.html('');
                return;
            }
            this.$el.html(QWeb.render('ShowAccountBankInfo', {
                bank_ids: info.content,
                title: info.title
            }));
        },
    });
    field_registry.add('bankinfo', ShowBankInfoWidget);
});
