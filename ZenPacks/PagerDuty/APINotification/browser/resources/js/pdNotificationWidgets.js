(function(){
    Ext.onReady(function() {
        var services_router = Zenoss.remote.ServicesRouter;

        /**
         * Frontend definition of a service
         */
        Ext.define('pagerduty.model.Service', {
            extend: 'Ext.data.Model',
            fields: [
                {name: 'name',        type: 'string'},
                {name: 'id',          type: 'string'},
                {name: 'service_key', type: 'string'},
                {name: 'type',        type: 'string'}
            ]
        });

        /**
         * UI control that allows selecting a particular PagerDuty service.
         *
         * This control shows both a combo box with a list of available
         * services, as well as a text box containing just the service key.
         *
         * Editing the service key updates the combo box and selecting from
         * the combo box updates the service key.
         *
         * The list of services in the combo box is dynamically populated by
         * calling services_router.get_services, which in turn calls PagerDuty's
         * service API.  If the request to PagerDuty's service API fails for
         * any reason, the combo box is hidden and replaced with a text box
         * detailing the error message (service_list_error).
         */
        Ext.define('pagerduty.api.events.ServiceListWidget', {
            extend: 'Ext.container.Container',
            alias: 'widget.pagerduty-api-events-service-list',
            name: 'service_key',
            layout:'anchor',
            id: 'pdServiceList',
            defaults: {
                anchor: '100%'
            },
            initComponent: function() {
                var container = this;

                this.store = Ext.create('Zenoss.NonPaginatedStore', {
                    storeId: 'service_store',
                    root: 'data',
                    autoLoad: true,
                    model: 'pagerduty.model.Service',
                    loaded: false,
                    flex: 1,

                    proxy: {
                        type:'direct',
                        limitParam:undefined,
                        startParam:undefined,
                        pageParam:undefined,
                        sortParam: undefined,
                        directFn: services_router.get_services,
                        reader: {
                            type:'json',
                            root: 'data'
                        },
                        listeners: {
                            exception: function(proxy, response, operation, eOpts) {
                                if (response.result && response.result.inline_message)
                                {
                                    Ext.getCmp('pdServiceList').showError(response.result.inline_message);
                                }
                            }
                        }
                    },

                    isLoaded: function() {
                        return this.loaded;
                    },
                    listeners:  {
                        load: function() {
                            this.loaded = true;
                            var combo = Ext.getCmp('service_list_combo');
                            combo.synchronize();
                        }
                    }
                });

                var service_list_combo = Ext.create('Ext.form.field.ComboBox',
                    {
                        name: 'service_list_combo',
                        id: 'service_list_combo',
                        queryMode: 'local',
                        valueField: 'service_key',
                        displayField: 'name',
                        forceSelection: true,
                        fieldLabel: _t('Service'),
                        store: container.store,
                        listeners: {
                            select: function (combo, record, index) {
                                Ext.getCmp('service_key_textfield').synchronize(combo.value)
                            }
                        },
                        synchronize: function() {
                            // Make the combo box match the text field
                            var service_key = Ext.getCmp('service_key_textfield').value;
                            var service_record = this.findRecordByValue(service_key);
                            if (service_record) {
                                this.setValue(service_key);
                            } else {
                                this.setValue(null);
                            }
                        }
                    });

                var service_list_error = Ext.create('Ext.form.field.Text',
                    {
                        name: 'service_list_error',
                        id: 'service_list_error',
                        fieldLabel: _t('Service'),
                        hidden: true,
                        readOnly: true
                    });

                var service_key_textfield = Ext.create('Ext.form.field.Text',
                    {
                        name: 'service_key',
                        id: 'service_key_textfield',
                        fieldLabel: _t('Service API Key'),
                        listeners: {
                            change: function() {
                                if (this.synchronizing)
                                    return;

                                var store = Ext.data.StoreManager.lookup('service_store');
                                if (store.isLoaded()) {
                                    var combo = Ext.getCmp('service_list_combo');
                                    combo.synchronize();
                                }
                            }
                        },
                        synchronizing: false,
                        synchronize: function(value) {
                            // Make the text field match the combo box
                            this.synchronizing = true;
                            this.setValue(value);
                            this.synchronizing = false;
                        }
                    });

                this.items = [service_list_combo, service_list_error, service_key_textfield];

                if (this.value) {
                    service_key_textfield.setValue(this.value);
                }

                this.callParent(arguments);
            },
            showError: function(msg) {
                var service_list_error = Ext.getCmp('service_list_error');
                var service_list_combo = Ext.getCmp('service_list_combo');
                service_list_combo.hide();
                service_list_error.show();
                service_list_error.setValue(msg);
            }

        }); // Ext.define DetailsField

        /**
         * UI control to allow editing or arbitrary key/value pairs.
         *
         * This control just sets up an Ext.grid.Panel with a row editor
         * attached to it.  The underlying store is a JSON store and we
         * serialize it as a list of dictionaries to the hidden field named
         * 'details'.  The serialization looks like:
         *
         * [{key:device, value:${evt/device},
         *  {key:eventID, value:${evt/evid},
         *  ... ]
         */
        Ext.define('pagerduty.api.events.DetailsField', {
            extend: 'Ext.container.Container',
            alias: 'widget.pagerduty-api-events-details-field',

            initComponent: function() {
                var store = Ext.create('Ext.data.JsonStore', {
                    autoSync: true,
                    fields: [{name: 'key'}, {name: 'value'}],
                    proxy: {type: 'memory'},
                    listeners: {
                        write: function(store, operation) {
                            if (!hidden_field) {
                                return;
                            }

                            vs = [];

                            Ext.each(store.getRange(), function(record) {
                                if (record.data.key) {
                                    vs.push(record.data);
                                }
                            });

                            hidden_field.setValue(Ext.JSON.encode(vs));
                        }
                    }
                });

                var hidden_field = Ext.create('Ext.form.field.Hidden', {name: 'details'});

                var row_editor = Ext.create('Ext.grid.plugin.RowEditing');

                var grid_panel = Ext.create('Ext.grid.Panel', {
                    title: _t('Details'),
                    height: 200,
                    plugins: [row_editor],
                    store: store,

                    dockedItems: [{
                        xtype: 'toolbar',
                        store: store,
                        items: [{
                            text: 'Add',
                            iconCls: 'add_button',
                            handler: function() {
                                store.insert(0, {key: '', value: ''});
                                row_editor.startEdit(0, 0);
                            }
                        }, '-', {
                            itemId: 'delete',
                            text: 'Delete',
                            iconCls: 'delete',
                            handler: function() {
                                var selection = grid_panel.getView().getSelectionModel().getSelection()[0];
                                if (selection) {
                                    store.remove(selection);
                                    store.sync();
                                }
                            }
                        }]
                    }],

                    columns: [{
                        header: _t('Key'),
                        dataIndex: 'key',
                        editor: { xtype: 'textfield', allowBlank: true },
                        sortable: true,
                        width: 200
                    },{
                        header: _t('Value'),
                        dataIndex: 'value',
                        editor: { xtype: 'textfield', allowBlank: true },
                        sortable: true,
                        flex: 1
                    }]
                });

                this.items = [hidden_field, grid_panel];

                if (this.value) {
                    hidden_field.setValue(this.value);
                    store.loadData(Ext.JSON.decode(this.value));
                }

                this.callParent(arguments);
            }
        }); // Ext.define DetailsField
    }); // Ext.onReady
})(); // outer closure
