odoo.define('voip.tests', function (require) {
"use strict";

var FormView = require('web.FormView');
var ListView = require('web.ListView');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('voip', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    foo: {string: "Foo", type: "char", default: "My little Foo Value", searchable: true},
                },
                records: [
                    {id: 1, foo: "yop"},
                    {id: 2, foo: "blip"},
                    {id: 4, foo: "abc"},
                    {id: 3, foo: "gnap"},
                    {id: 5, foo: "blop"},
                ],
            },
        };
    },
}, function () {

    QUnit.module('PhoneWidget');

    QUnit.test('phone field in form view on normal screens', function (assert) {
        assert.expect(7);

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch:'<form string="Partners">' +
                    '<sheet>' +
                        '<group>' +
                            '<field name="foo" widget="phone"/>' +
                        '</group>' +
                    '</sheet>' +
                '</form>',
            res_id: 1,
            config: {
                device: {
                    size_class: 1, // Screen SM
                    SIZES: { XS: 0, SM: 1, MD: 2, LG: 3 },
                }
            },
        });

        var $phoneLink = form.$('a.o_form_uri.o_field_widget');
        assert.strictEqual($phoneLink.length, 1,
            "should have a anchor with correct classes");
        assert.strictEqual($phoneLink.text(), 'y\u00ADop',
            "value should be displayed properly as text with the skype obfuscation");
        assert.strictEqual($phoneLink.attr('href'), 'tel:yop',
            "should have proper tel prefix");

        // switch to edit mode and check the result
        form.$buttons.find('.o_form_button_edit').click();
        assert.strictEqual(form.$('input[type="text"].o_field_widget').length, 1,
            "should have an input for the phone field");
        assert.strictEqual(form.$('input[type="text"].o_field_widget').val(), 'yop',
            "input should contain field value in edit mode");

        // change value in edit mode
        form.$('input[type="text"].o_field_widget').val('new').trigger('input');

        // save
        form.$buttons.find('.o_form_button_save').click();
        $phoneLink = form.$('a.o_form_uri.o_field_widget');
        assert.strictEqual($phoneLink.text(), 'n\u00ADew',
            "new value should be displayed properly as text with the skype obfuscation");
        assert.strictEqual($phoneLink.attr('href'), 'tel:new',
            "should still have proper tel prefix");

        form.destroy();
    });

    QUnit.test('phone field in editable list view on normal screens', function (assert) {
        assert.expect(10);

        var list = createView({
            View: ListView,
            model: 'partner',
            data: this.data,
            arch: '<tree editable="bottom"><field name="foo"  widget="phone"/></tree>',
            config: {
                device: {
                    size_class: 1, // Screen SM
                    SIZES: { XS: 0, SM: 1, MD: 2, LG: 3 },
                }
            },
        });

        assert.strictEqual(list.$('tbody td:not(.o_list_record_selector)').length, 5,
            "should have 5 cells");
        assert.strictEqual(list.$('tbody td:not(.o_list_record_selector)').first().text(), 'y\u00ADop',
            "value should be displayed properly as text with the skype obfuscation");

        var $phoneLink = list.$('a.o_form_uri.o_field_widget');
        assert.strictEqual($phoneLink.length, 5,
            "should have anchors with correct classes");
        assert.strictEqual($phoneLink.first().attr('href'), 'tel:yop',
            "should have proper tel prefix");

        // Edit a line and check the result
        var $cell = list.$('tbody td:not(.o_list_record_selector)').first();
        $cell.click();
        assert.ok($cell.parent().hasClass('o_selected_row'), 'should be set as edit mode');
        assert.strictEqual($cell.find('input').val(), 'yop',
            'should have the corect value in internal input');
        $cell.find('input').val('new').trigger('input');

        // save
        list.$buttons.find('.o_list_button_save').click();
        $cell = list.$('tbody td:not(.o_list_record_selector)').first();
        assert.ok(!$cell.parent().hasClass('o_selected_row'), 'should not be in edit mode anymore');
        assert.strictEqual(list.$('tbody td:not(.o_list_record_selector)').first().text(), 'n\u00ADew',
            "value should be properly updated");
        $phoneLink = list.$('a.o_form_uri.o_field_widget');
        assert.strictEqual($phoneLink.length, 5,
            "should still have anchors with correct classes");
        assert.strictEqual($phoneLink.first().attr('href'), 'tel:new',
            "should still have proper tel prefix");

        list.destroy();
    });

});
});
