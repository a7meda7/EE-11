odoo.define('web_studio.ActionEditorSidebar', function (require) {
"use strict";

var core = require('web.core');
var relational_fields = require('web.relational_fields');
var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
var Widget = require('web.Widget');

var Many2ManyTags = relational_fields.FieldMany2ManyTags;

var ActionEditorSidebar = Widget.extend(StandaloneFieldManagerMixin, {
    template: 'web_studio.ActionEditorSidebar',
    events: {
        'change input, textarea': '_onActionChange',
        'click .o_web_studio_parameters': '_onParameters',
    },
    /**
     * @constructor
     * @param {Object} action
     */
    init: function (parent, action) {
        this._super.apply(this, arguments);
        StandaloneFieldManagerMixin.init.call(this);

        this.debug = core.debug;
        this.action = action;
        this.action_attrs = {
            name: action.display_name || action.name,
            help: action.help && action.help.replace(/\n\s+/g, '\n') || '',
        };
    },
    /**
     * @override
     */
    willStart: function () {
        var self = this;
        var def1 = this.model.makeRecord('ir.actions.act_window', [{
            name: 'groups_id',
            fields: [{
                name: 'id',
                type: 'integer',
            }, {
                name: 'display_name',
                type: 'char',
            }],
            relation: 'res.groups',
            type: 'many2many',
            value: this.action.groups_id,
        }]).then(function (recordID) {
            self.groupsHandle = recordID;
        });
        var def2 = this._super.apply(this, arguments);
        return $.when(def1, def2);
    },
    /**
     * @override
     */
    start: function () {
        var def1 = this._super.apply(this, arguments);
        var record = this.model.get(this.groupsHandle);
        var options = {
            mode: 'edit',
        };
        var many2many = new Many2ManyTags(this, 'groups_id', record, options);
        this._registerWidget(this.groupsHandle, 'groups_id', many2many);
        var def2 = many2many.appendTo(this.$('.o_groups'));
        return $.when(def1, def2);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} event
     */
    _onActionChange: function (event) {
        var $input = $(event.currentTarget);
        var attribute = $input.attr('name');
        if (attribute) {
            var new_attrs = {};
            new_attrs[attribute] = $input.val();
            this.trigger_up('studio_edit_action', {args: new_attrs});
        }
    },

    /**
     * @private
     */
    _onParameters: function () {
        this.trigger_up('parameters_clicked');
    },

    /*
     * @private
     * @override
     */
    _onFieldChanged: function () {
        StandaloneFieldManagerMixin._onFieldChanged.apply(this, arguments);
        var record = this.model.get(this.groupsHandle);
        var args = {
            groups_id: record.data.groups_id.res_ids,
        };
        this.trigger_up('studio_edit_action', {args: args});
    },
});

return ActionEditorSidebar;

});
