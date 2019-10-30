odoo.define('grouped_by_list_view_editable.grouped_by_list_view_editable', function (require) {
    "use strict";


    var ListView = require('web.ListView');

    ListView.prototype.defaults.editable = null;

    ListView.include({

        isEditable: function (params) {
            params.readonly = false
            return !this.options.disable_editable_mode
                && (this.fields_view.arch.attrs.editable || this._context_editable || this.options.editable);
        },
    });


});
