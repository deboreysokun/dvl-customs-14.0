odoo.define("web_tree_decoration_custom.ListRenderer", function (require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");
    var py = window.py;
    var customDecorations = {
        'decoration-bg-gray': 'bg-gray',
        'decoration-bg-purple': 'bg-purple',
        'decoration-bg-red': 'bg-red',
        'decoration-bg-blue': 'bg-blue',
        'decoration-bg-white': 'bg-white',
        'decoration-bg-brown': 'bg-brown',
        'decoration-bg-green': 'bg-green',
        'decoration-bg-yellow': 'bg-yellow',
        'decoration-bg-pink': 'bg-pink',
    }

    ListRenderer.include({
        init: function () {
            this._super.apply(this, arguments);
            Object.entries(customDecorations).forEach(([attribute, bgclass]) => {
                if (attribute in this.arch.attrs) {
                    var bg_color = py.parse(py.tokenize(this.arch.attrs[attribute]));
                    this.rowDecorations[bgclass] = bg_color;
                }
            });
        },
    });
});
