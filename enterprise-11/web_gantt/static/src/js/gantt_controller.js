odoo.define('web_gantt.GanttController', function (require) {
"use strict";

var AbstractController = require('web.AbstractController');
var core = require('web.core');
var config = require('web.config');
var Dialog = require('web.Dialog');
var dialogs = require('web.view_dialogs');
var time = require('web.time');

var _t = core._t;
var qweb = core.qweb;


var GanttController = AbstractController.extend({
    events: {
        'click .gantt_task_row .gantt_task_cell': '_onCreateClick',
    },
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        task_changed: '_onTaskChanged',
        task_display: '_onTaskDisplay',
        task_create: '_onTaskCreate',
    }),

    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.set('title', params.title);
        this.context = params.context;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Render the buttons according to the GanttView.buttons template and add
     * listeners on it. Set this.$buttons with the produced jQuery element
     *
     * @param {jQuery} [$node] a jQuery node where the rendered buttons should
     *   be inserted $node may be undefined, in which case they are inserted
     *   into this.options.$buttons
     */
    renderButtons: function ($node) {
        var self = this;
        if ($node) {
            this.$buttons = $(qweb.render("GanttView.buttons", {'isMobile': config.device.isMobile}));
            this.$buttons.appendTo($node);
            this.$buttons.find('.o_gantt_button_scale').bind('click', function (event) {
                self.$buttons.find('.dropdown_gantt_content').text($(this).text());
                self.$buttons.find('.o_gantt_button_scale').removeClass('active');
                self.$buttons.find(this).addClass('active');
                return self._setScale($(event.target).data('value'));
            });
            this.$buttons.find('.o_gantt_button_left').bind('click', function () {
                var state = self.model.get();
                self._focusDate(state.focus_date.subtract(1, state.scale));
            });
            this.$buttons.find('.o_gantt_button_right').bind('click', function () {
                var state = self.model.get();
                self._focusDate(state.focus_date.add(1, state.scale));
            });
            this.$buttons.find('.o_gantt_button_today').bind('click', function () {
                self.model.setFocusDate(moment(new Date()));
                return self.reload();
            });
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {string} id
     * @param {Moment} startDate
     */
    _createTask: function (id, startDate) {
        var task = gantt.getTask(id);

        var end_date;
        switch (this.model.get().scale) {
            case "day":
                end_date = startDate.clone().add(4, "hour");
                break;
            case "week":
                end_date = startDate.clone().add(2, "day");
                break;
            case "month":
                end_date = startDate.clone().add(4, "day");
                break;
            case "year":
                end_date = startDate.clone().add(2, "month");
                break;
        }

        var context = _.clone(this.context);
        var get_create = function (item) {
            if (item.create) {
                context["default_"+item.create[0]] = item.create[1][0];
            }
            if (item.parent) {
                var parent = gantt.getTask(item.parent);
                get_create(parent);
            }
        };
        get_create(task);

        context["default_"+this.model.mapping.date_start] = startDate.format("YYYY-MM-DD HH:mm:ss");
        if(this.model.mapping.date_stop) {
            context["default_"+this.model.mapping.date_stop] = end_date.format("YYYY-MM-DD HH:mm:ss");
        } else { // We assume date_delay is given
            context["default_"+this.model.mapping.date_delay] = gantt.calculateDuration(startDate, end_date);
        }

        context.id = 0;

        this._displayTask(context);
    },
    /**
     * Dialog to edit/display a task.
     *
     * @private
     * @param {Object} task
     */
    _displayTask: function (task) {
        var task_id = _.isString(task.id) ? parseInt(_.last(task.id.split("_")), 10) : task.id;

        new dialogs.FormViewDialog(this, {
            res_model: this.modelName,
            res_id: task_id,
            context: task,
            on_saved: this.reload.bind(this)
        }).open();
    },
    /**
     * @private
     * @param {Moment} focusDate
     */
    _focusDate: function (focusDate) {
        var self = this;
        this.model.setFocusDate(focusDate);
        this.reload().then(function () {
            self.set({'title': _t('Forecast') + ' (' + self.model.get().date_display + ')'});
        });
    },
    /**
     * @private
     * @param {any} scale
     */
    _setScale: function (scale) {
        var self = this;
        this.model.setScale(scale);
        this.reload().then(function () {
            self.set({'title': _t('Forecast') + ' (' + self.model.get().date_display + ')'});
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handler used when clicking on an empty cell. The behaviour is to create a
     * new task and apply some default values.
     *
     * @private
     * @param {MouseEvent} event
     */
    _onCreateClick: function (event) {
        var id = event.target.parentElement.attributes.task_id.value;
        var class_date = _.find(event.target.classList, function (e) {
            return e.indexOf("date_") > -1;
        });
        var start_date = moment(new Date(parseInt(class_date.split("_")[1], 10))).utc();

        this._createTask(id, start_date);
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onTaskChanged: function (event) {
        var task_obj = event.data.task;
        var success = event.data.success;
        var fail = event.data.fail;
        var fields = this.model.fields;
        // TODO: modify date_delay instead of date_stop
        if (fields[this.model.mapping.date_stop] === undefined) {
            // Using a duration field instead of date_stop
            Dialog.alert(this, _t('You have no date_stop field defined!'));
            return fail();
        }
        // We first check that the fields aren't defined as readonly.
        if (fields[this.model.mapping.date_start].readonly || fields[this.model.mapping.date_stop].readonly) {
            Dialog.alert(this, _t('You are trying to write on a read-only field!'));
            return fail();
        }

        // Now we try to write the new values in the dataset. Note that it may fail
        // if the constraints defined on the model aren't met.
        var start = task_obj.start_date;
        var end = task_obj.end_date;
        var data = {};
        data[this.model.mapping.date_start] = time.auto_date_to_str(start, fields[this.model.mapping.date_start].type);
        if (this.model.mapping.date_stop) {
            // If date_stop is a date, we should write the previous day since it is considered as
            // included.
            var field_type = fields[this.model.mapping.date_stop].type;
            if (field_type === 'date') {
                end.setTime(end.getTime() - 86400000);
                data[this.model.mapping.date_stop] = time.auto_date_to_str(end, field_type);
                end.setTime(end.getTime() + 86400000);
            } else {
                data[this.model.mapping.date_stop] = time.auto_date_to_str(end, field_type);
            }
        } else { // we assume date_duration is defined
            var duration = gantt.calculateDuration(start, end);
            data[this.model.mapping.date_delay] = duration;
        }
        var task_id = parseInt(task_obj.id.split("gantt_task_").slice(1)[0], 10);

        this._rpc({
                model: this.model.modelName,
                method: 'write',
                args: [task_id, data],
            })
            .then(success, fail);
    },
    /**
     * Dialog to create a task.
     *
     * @private
     */
    _onTaskCreate: function () {
        var start_date = moment(new Date()).utc();
        this._createTask(0, start_date);
    },
    /**
     * Dialog to edit/display a task.
     *
     * @private
     * @param {OdooEvent} event
     */
    _onTaskDisplay: function (event) {
        this._displayTask(event.data);
    },


});

return GanttController;

});
