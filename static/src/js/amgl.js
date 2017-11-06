function join_name(names) {
    var str = "";
    var step;
    for (step = 0; step < names.length; step++) {
        str = str + (step + 1) + '- ' + names[step].full_name + ' \n';
    };
    return str;
}

odoo.define('amgl.web.ListView', function (require) {
    "use strict";

    // put an alert here and refresh the page if the alert don't appear
    // than the javascript file is not loaded at all you need to upgrade
    // you module
    var core = require('web.core');
    var _t = core._t;
    var Model = require('web.DataModel');
    // the Class is saved in view_registry
    // Note same thing for widgets,widgets for form view are saved in : form_widget_registry
    // always look for the key and get them using that key
    // in odoo 10.0 if you look at list_view.js you will find this line:
    // core.view_registry.add('list', ListView);
    // here he saved the class with key 'list'
    var ListView = core.view_registry.get('list');
    // just override the do_delete methd
    ListView.include({
        reload_content: synchronized(function () {
            var self = this;
            this.setup_columns(this.fields_view.fields, this.grouped);
            this.$('tbody .o_list_record_selector input').prop('checked', false);
            this.records.reset();
            var reloaded = $.Deferred();
            this.groups.render(function () {
                if (self.dataset.index === null) {
                    if (self.records.length) {
                        self.dataset.index = 0;
                    }
                } else if (self.dataset.index >= self.records.length) {
                    self.dataset.index = self.records.length ? 0 : null;
                }
                self.load_list().then(function () {
                    if (!self.grouped && self.display_nocontent_helper()) {
                        self.no_result();
                    }
                    reloaded.resolve();
                });
            });
            this.do_push_state({
                min: this.current_min,
                limit: this._limit
            });
            console.log($('table'));
            $("table").resizableColumns({
                store: window.store
            });
            return reloaded.promise();
        }),
        do_load_state: function (state, warm) {
            var reload = false;
            if (state.min && this.current_min !== state.min) {
                this.current_min = state.min;
                reload = true;
            }
            if (state.limit) {
                if (_.isString(state.limit)) {
                    state.limit = null;
                }
                if (state.limit !== this._limit) {
                    this._limit = state.limit;
                    reload = true;
                }
            }
            if (reload) {
                this.reload_content();
            }
            console.log($('table'));
            $("table").resizableColumns({
                store: window.store
            });
        },
        do_delete: function (ids) {
            console.log('override the function don again'); // to make sure
            if (this.model == 'amgl.customer') {
                var self = this;
                new Model(self.model).call('read', [ids, ['full_name'], this.dataset.get_context()])
                .done(function (names) {
                    var text = _t("Do you really want to remove these records?") + ' \n \n' + join_name(names)
                    if (!(ids.length && confirm(text))) {
                        return;
                    }
                    return $.when(self.dataset.unlink(ids)).done(function () {
                        _(ids).each(function (id) {
                            self.records.remove(self.records.get(id));
                        });
                        // Hide the table if there is no more record in the dataset
                        if (self.display_nocontent_helper()) {
                            self.no_result();
                        } else {
                            if (self.records.length && self.current_min === 1) {
                                // Reload the list view if we delete all the records of the first page
                                self.reload();
                            } else if (self.records.length && self.dataset.size() > 0) {
                                // Load previous page if the current one is empty
                                self.pager.previous();
                            }
                            // Reload the list view if we are not on the last page
                            if (self.current_min + self._limit - 1 < self.dataset.size()) {
                                self.reload();
                            }
                        }
                        self.update_pager(self.dataset);
                        self.compute_aggregates();
                    });
                });
            }
            else {
                if (!(ids.length && confirm(_t("Do you really want to remove these records?")))) {
                    return;
                }
                var self = this;
                return $.when(this.dataset.unlink(ids)).done(function () {
                    _(ids).each(function (id) {
                        self.records.remove(self.records.get(id));
                    });
                    // Hide the table if there is no more record in the dataset
                    if (self.display_nocontent_helper()) {
                        self.no_result();
                    } else {
                        if (self.records.length && self.current_min === 1) {
                            // Reload the list view if we delete all the records of the first page
                            self.reload();
                        } else if (self.records.length && self.dataset.size() > 0) {
                            // Load previous page if the current one is empty
                            self.pager.previous();
                        }
                        // Reload the list view if we are not on the last page
                        if (self.current_min + self._limit - 1 < self.dataset.size()) {
                            self.reload();
                        }
                    }
                    self.update_pager(self.dataset);
                    self.compute_aggregates();
                });
            }
        },
    });

});