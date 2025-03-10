import random
import textwrap
from odoo.http import _request_stack
from odoo.tests.common import TransactionCase
from odoo.addons.web_studio.controllers.main import WebStudioController


class TestViewNormalization(TransactionCase):

    maxDiff = None

    def setUp(self):
        super(TestViewNormalization, self).setUp()
        random.seed('https://youtu.be/tFjNH9l6-sQ')
        _request_stack.push(self)
        self.base_view = self.env.ref('base.view_partner_form')
        self.gantt_view = self.env['ir.ui.view'].create({
            'arch_base':
            """
            <gantt date_start="date" date_stop="" string="Test">
            </gantt>
            """,
            'model': 'res.partner',
            'type': 'gantt',
        })
        self.view = self.base_view.create({
            'arch_base':
            """
            <form string="Partners">
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="toggle_active" type="object" groups="base.group_no_one" class="oe_stat_button" icon="fa-archive">
                            <field name="active" widget="boolean_button" options="{&quot;terminology&quot;: &quot;archive&quot;}"/>
                        </button>
                    </div>
                    <field name="image" widget="image" class="oe_avatar" options="{&quot;preview_image&quot;: &quot;image_medium&quot;, &quot;size&quot;: [90, 90]}"/>
                    <div class="oe_title">
                        <field name="is_company" invisible="1"/>
                        <field name="company_type" widget="radio" class="oe_edit_only" on_change="on_change_company_type(company_type)" options="{'horizontal': true}"/>
                        <h1>
                            <field name="name" default_focus="1" placeholder="Name" attrs="{'required' : [('type', '=', 'contact')]}"/>
                        </h1>
                        <div class="o_row">
                            <field name="parent_id" placeholder="Company" domain="[('is_company', '=', True)]" context="{'default_is_company': True}" attrs="{'invisible': [('is_company','=', True),('parent_id', '=', False)]}" on_change="onchange_parent_id(parent_id)"/>
                        </div>
                    </div>

                    <group>
                        <group>
                            <field name="type" attrs="{'invisible': [('parent_id','=', False)]}" groups="base.group_no_one"/>
                            <label for="street" string="Address"/>
                            <div class="o_address_format">
                                <div class="oe_edit_only">
                                    <button name="open_parent" type="object" string="(edit)" class="oe_link" attrs="{'invisible': ['|', ('parent_id', '=', False), ('type', '!=', 'contact')]}"/>
                                </div>

                                <field name="street" placeholder="Street..." class="o_address_street" attrs="{'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]}"/>
                                <field name="street2" placeholder="Street 2..." class="o_address_street" attrs="{'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]}"/>
                                <field name="city" placeholder="City" class="o_address_city" attrs="{'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]}"/>
                                <field name="state_id" class="o_address_state" placeholder="State" options="{&quot;no_open&quot;: True}" on_change="onchange_state(state_id)" attrs="{'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]}" context="{'country_id': country_id, 'zip': zip}"/>
                                <field name="zip" placeholder="ZIP" class="o_address_zip" attrs="{'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]}"/>
                                <field name="country_id" placeholder="Country" class="o_address_country" options="{&quot;no_open&quot;: True, &quot;no_create&quot;: True}" attrs="{'readonly': [('type', '=', 'contact'),('parent_id', '!=', False)]}"/>
                            </div>
                            <field name="website" widget="url" placeholder="e.g. www.odoo.com"/>
                        </group>
                        <group>
                            <field name="function" placeholder="e.g. Sales Director" attrs="{'invisible': [('is_company','=', True)]}"/>
                            <field name="phone" widget="phone"/>
                            <field name="mobile" widget="phone"/>
                            <field name="user_ids" invisible="1"/>
                            <field name="email" widget="email" attrs="{'required': [('user_ids','!=', [])]}"/>
                            <field name="title" options="{&quot;no_open&quot;: True}" attrs="{'invisible': [('is_company', '=', True)]}"/>
                            <field name="lang"/>
                            <field name="category_id" widget="many2many_tags" placeholder="Tags..."/>
                        </group>
                    </group>

                    <notebook colspan="4">
                        <page string="Contacts &amp; Addresses" autofocus="autofocus">
                            <field name="child_ids" mode="kanban" context="{'default_parent_id': active_id, 'default_street': street, 'default_street2': street2, 'default_city': city, 'default_state_id': state_id, 'default_zip': zip, 'default_country_id': country_id}">
                                <kanban>
                                    <field name="color"/>
                                    <field name="name"/>
                                    <field name="title"/>
                                    <field name="type"/>
                                    <field name="email"/>
                                    <field name="parent_id"/>
                                    <field name="is_company"/>
                                    <field name="function"/>
                                    <field name="phone"/>
                                    <field name="street"/>
                                    <field name="street2"/>
                                    <field name="zip"/>
                                    <field name="city"/>
                                    <field name="country_id"/>
                                    <field name="mobile"/>
                                    <field name="state_id"/>
                                    <field name="image"/>
                                    <templates>
                                        <t t-name="kanban-box">
                                            <div class="oe_kanban_details">
                                                <field name="name"/>
                                            </div>
                                        </t>
                                    </templates>
                                </kanban>
                            </field>
                        </page>
                    </notebook>
                </sheet>
            </form>
            """,
            'model': 'res.partner'})
        self.studio_controller = WebStudioController()

    def _test_view_normalization(self, original, expected, view='form'):
        if view == 'gantt':
            view = self.gantt_view
        else:
            view = self.view

        original = original and textwrap.dedent(original)
        self.studio_controller._set_studio_view(view, original)

        studio_view = self.studio_controller._get_studio_view(view)
        studio_view = studio_view.with_context(load_all_views=True)
        normalized = studio_view.normalize()

        self.studio_controller._set_studio_view(view, normalized)
        self.env[self.view.model].with_context(studio=True, load_all_views=True).fields_view_get(view.id, view.type)

        normalized = normalized and normalized.strip()
        expected = expected and textwrap.dedent(expected).strip()
        self.assertEqual(normalized, expected)

    # Flatten all xpath that target nodes added by studio itself
    def test_view_normalization_00(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="/form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <group name="studio_group_E16QG_left" string="Left Title"/>
                  <group name="studio_group_E16QG_right" string="Right Title"/>
                </group>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_left']" position="inside">
                <field name="credit_limit"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_left']" position="after">
                <field name="id"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="inside">
                <field name="employee"/>
              </xpath>
              <xpath expr="//field[@name='credit_limit']" position="after">
                <field name="contact_address"/>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <group name="studio_group_E16QG_left" string="Left Title">
                    <field name="credit_limit"/>
                    <field name="contact_address"/>
                  </group>
                  <field name="id"/>
                  <group name="studio_group_E16QG_right" string="Right Title">
                    <field name="employee"/>
                  </group>
                </group>
              </xpath>
            </data>
        """)

    # Delete children of deleted nodes and reanchor siblings
    def test_view_normalization_01(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="/form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <group name="studio_group_E16QG_left" string="Left Title"/>
                  <group name="studio_group_E16QG_right" string="Right Title"/>
                </group>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_left']" position="inside">
                <field name="credit_limit"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_left']" position="after">
                <field name="id"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="inside">
                <field name="employee"/>
              </xpath>
              <xpath expr="//field[@name='credit_limit']" position="after">
                <field name="contact_address"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_left']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <field name="id"/>
                  <group name="studio_group_E16QG_right" string="Right Title">
                    <field name="employee"/>
                  </group>
                </group>
              </xpath>
            </data>
        """)

    # When there is no more sibling, we need to reanchor on the parent
    def test_view_normalization_02(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="/form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <group name="studio_group_E16QG_right" string="Right Title"/>
                </group>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="before">
                <field name="id"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="inside">
                <field name="employee"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <field name="id"/>
                </group>
              </xpath>
            </data>
        """)

    # When a field is deleted, other xpath that targets it need to be reanchored.
    def test_view_normalization_03(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="/form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <group name="studio_group_E16QG_right" string="Right Title"/>
                </group>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="before">
                <field name="id"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="inside">
                <field name="employee"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG_right']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG">
                  <field name="id"/>
                </group>
              </xpath>
            </data>
        """)

    # If there is nothing left in the studio view, delete it.
    def test_view_normalization_04(self):
        expected = ''
        self._test_view_normalization("""
            <data>
              <xpath expr="/form[1]/sheet[1]/group[1]" position="after">
                <group name="studio_group_E16QG"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG']" position="inside">
                <field name="id"/>
              </xpath>
              <xpath expr="//field[@name='id']" position="after">
                <field name="create_uid"/>
              </xpath>
              <xpath expr="//group[@name='studio_group_E16QG']" position="replace"/>
            </data>
        """, expected)
        studio_view = self.studio_controller._set_studio_view(self.view, expected)
        studio_view = self.studio_controller._get_studio_view(self.view)
        self.assertEqual(len(studio_view), 0)

    # An after can become a replace if the following sibling has been removed.
    def test_view_normalization_05(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='mobile']" position="after">
                <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='mobile']" position="replace"/>
              <xpath expr="//field[@name='contact_address']" position="after">
                <field name="tz"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='mobile']" position="replace">
                <field name="tz"/>
              </xpath>
            </data>
        """)

    # Multiple additions of fields should not appear if it was deleted
    def test_view_normalization_06(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='website']" position="after">
                <field name="color"/>
              </xpath>
              <xpath expr="//field[@name='color']" position="replace">
              </xpath>
              <xpath expr="//field[@name='category_id']" position="after">
                <field name="color"/>
              </xpath>
              <xpath expr="//field[@name='color']" position="after">
                <field name="create_date"/>
              </xpath>
              <xpath expr="//field[@name='color']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//field[@name='category_id']" position="after">
                <field name="create_date"/>
              </xpath>
            </data>
        """)

    # Consecutive xpaths around a field that was moved away can be merged.
    def test_view_normalization_07(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='mobile']" position="after">
                <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="after">
                  <field name="tz"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="replace"/>
              <xpath expr="//field[@name='tz']" position="after">
                  <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="after">
                  <field name="create_uid"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='mobile']" position="after">
                <field name="tz"/>
                <field name="create_uid"/>
              </xpath>
            </data>
        """)

    # A field that was added, then moved then deleted should not appear.
    def test_view_normalization_08(self):
        self._test_view_normalization("""
          <data>
            <xpath expr="//field[@name='website']" position="after">
              <field name="color"/>
            </xpath>
            <xpath expr="//field[@name='color']" position="replace">
              <field name="create_uid"/>
            </xpath>
            <xpath expr="//field[@name='category_id']" position="after">
              <field name="color"/>
            </xpath>
            <xpath expr="//field[@name='color']" position="after">
              <field name="create_date"/>
            </xpath>
            <xpath expr="//field[@name='color']" position="replace"/>
          </data>
        """, """
          <data>
            <xpath expr="//field[@name='website']" position="after">
              <field name="create_uid"/>
            </xpath>
            <xpath expr="//field[@name='category_id']" position="after">
              <field name="create_date"/>
            </xpath>
          </data>
        """)

    # Fields that were added then removed should not appear in the view at all,
    # and every other xpath that was using it should be reanchored elsewhere.
    def test_view_normalization_09(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='phone']" position="after">
                <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="replace">
                  <field name="id"/>
              </xpath>
              <xpath expr="//field[@name='mobile']" position="after">
                  <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="after">
                  <field name="create_uid"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='phone']" position="after">
                <field name="id"/>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='mobile']" position="after">
                <field name="create_uid"/>
              </xpath>
            </data>
        """)

    # When two fields are added after a given field, the second one will appear
    # before the first one.
    def test_view_normalization_10(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='phone']" position="replace">
                <field name="create_date"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="after">
                  <field name="id"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="after">
                <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='phone']" position="replace">
                <field name="contact_address"/>
                <field name="id"/>
              </xpath>
            </data>
        """)

    # When we add a field after another one and replace the sibling of this one,
    # everything could be done in a single replace on the sibling node.
    def test_view_normalization_11(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='phone']" position="after">
                <field name="create_uid"/>
              </xpath>
              <xpath expr="//field[@name='phone']" position="replace">
                <field name="create_date"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="after">
                  <field name="id"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="replace"/>
              <xpath expr="//field[@name='create_uid']" position="before">
                <field name="create_date"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="after">
                  <field name="mobile"/>
              </xpath>
              <xpath expr="//field[@name='create_date']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='phone']" position="replace">
                <field name="id"/>
                <field name="mobile"/>
                <field name="create_uid"/>
              </xpath>
            </data>
        """)

    # When closest previous node has no name, the closest next node should be
    # used instead, provided it has a name. Also, attributes need to be handled
    # in a single xpath and alphabetically sorted.
    def test_view_normalization_12(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="attributes">
                <attribute name="zzz">PAGE 1 ZZZ</attribute>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="after">
                <page name="PAGE_2" string="AWESOME PAGE 2"/>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="attributes">
                <attribute name="help">PAGE 1 HELP</attribute>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="attributes">
                <attribute name="help">PAGE 1 HELP</attribute>
                <attribute name="zzz">PAGE 1 ZZZ</attribute>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]" position="inside">
                <page name="PAGE_2" string="AWESOME PAGE 2"/>
              </xpath>
            </data>
        """)

    # Changing an already existing attribute will generate a remove line for
    # the previous value and an addition line for the new value. The removing
    # line should not close the attributes xpath, both attributes need to be
    # redefined in a single xpath.
    def test_view_normalization_13(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="attributes">
                <attribute name="string">PAGE 1</attribute>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="after">
                <page name="PAGE_2" string="AWESOME PAGE 2"/>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="attributes">
                <attribute name="help">PAGE 1 HELP</attribute>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]" position="attributes">
                <attribute name="help">PAGE 1 HELP</attribute>
                <attribute name="string">PAGE 1</attribute>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]" position="inside">
                <page name="PAGE_2" string="AWESOME PAGE 2"/>
              </xpath>
            </data>
        """)

    def test_view_normalization_14(self):
        # There is already a chatter on res.partner.form view, which is why
        # the resulting xpath is /div instead of /sheet.
        self._test_view_normalization("""
            <data>
              <xpath expr="/form[1]/*[last()]" position="after">
                <div class="oe_chatter">
                  <field name="message_follower_ids" widget="mail_followers"/>
                  <field name="message_ids" widget="mail_thread"/>
                </div>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]" position="after">
                <div class="oe_chatter" name="studio_div_302a40">
                  <field name="message_follower_ids" widget="mail_followers"/>
                  <field name="message_ids" widget="mail_thread"/>
                </div>
              </xpath>
            </data>
        """)

    # Don't break on text with newlines
    def test_view_normalization_15(self):
        # New lines in text used to create a new line in the diff, desynchronizing
        # the diff lines and the tree elements iterator
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='phone']" position="replace">
                <h1>
                    THIS
                    IS
                    A MULTILINE
                    TITLE
                </h1>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='phone']" position="replace">
                <h1>
                    THIS
                    IS
                    A MULTILINE
                    TITLE
                </h1>
              </xpath>
            </data>
        """)

    # Test anchoring next to studio fields
    def test_view_normalization_16(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='mobile']" position="after">
                <field name="contact_address"/>
              </xpath>
              <xpath expr="//field[@name='contact_address']" position="after">
                <field name="tz"/>
              </xpath>
              <xpath expr="//field[@name='tz']" position="before">
                <field name="phone"/>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='mobile']" position="after">
                <field name="contact_address"/>
                <field name="phone"/>
                <field name="tz"/>
              </xpath>
            </data>
        """)

    # Test replace of last element in arch
    def test_view_normalization_17(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='lang']" position="replace"/>
            </data>
        """, """
            <data>
              <xpath expr="//field[@name='lang']" position="replace"/>
            </data>
        """)

    # Replace an existing element then add it back in but somewhere before
    # its original position
    def test_view_normalization_18(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='mobile']" position="replace"/>
              <xpath expr="//field[@name='function']" position="after">
                <field name="mobile" widget="phone"/>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='mobile']" position="replace"/>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='function']" position="after">
                <field name="mobile" widget="phone"/>
              </xpath>
            </data>
        """)

    # Delete an existing element, then replace another element with the deleted
    # element further down
    def test_view_normalization_19(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='phone']" position="replace"/>
              <xpath expr="//field[@name='email']" position="replace"/>
              <xpath expr="//field[@name='user_ids']" position="after">
                <field name="phone"/>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='email']" position="replace">
                <field name="phone"/>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='phone']" position="replace"/>
            </data>
        """)

    # Delete an existing element, then replace another element before the
    # original element with the latter
    def test_view_normalization_20(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//field[@name='email']" position="replace"/>
              <xpath expr="//field[@name='phone']" position="replace"/>
              <xpath expr="//field[@name='function']" position="after">
                <field name="email"/>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='email']" position="replace"/>
              <xpath expr="//form[1]/sheet[1]/group[1]/group[2]/field[@name='phone']" position="replace">
                <field name="email"/>
              </xpath>
            </data>
        """)

    # template fields are appended to the templates, not to the kanban itself
    def test_view_normalization_21(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//templates//field[@name='name']" position="after">
                <field name="phone"/>
              </xpath>
              <xpath expr="//templates//field[@name='phone']" position="after">
                <field name="mobile"/>
              </xpath>
              <xpath expr="//templates//field[@name='name']" position="before">
                <field name="color"/>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]/field[@name='child_ids']/kanban[1]/templates[1]/t[1]/div[1]/field[@name='name']" position="before">
                <field name="color"/>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]/field[@name='child_ids']/kanban[1]/templates[1]/t[1]/div[1]/field[@name='name']" position="after">
                <field name="phone"/>
                <field name="mobile"/>
              </xpath>
            </data>
        """)

    # adding kanban and template fields while using absolute xpaths
    def test_view_normalization_22(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//templates" position="before">
                <field name="lang"/>
              </xpath>
              <xpath expr="//templates//div" position="inside">
                <div class="o_dropdown_kanban dropdown">
                            <a class="dropdown-toggle btn" data-toggle="dropdown" href="#">
                                <span class="fa fa-bars fa-lg"/>
                            </a>
                            <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel">
                                <t t-if="widget.editable"><li><a type="edit">Edit</a></li></t>
                                <t t-if="widget.deletable"><li><a type="delete">Delete</a></li></t>
                                <li><ul class="oe_kanban_colorpicker" data-field="lang"/></li>
                            </ul>
                        </div>
              </xpath>
              <xpath expr="//templates//div" position="attributes">
                <attribute name="color">lang</attribute>
              </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]/field[@name='child_ids']/kanban[1]/field[@name='image']" position="after">
                <field name="lang"/>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]/field[@name='child_ids']/kanban[1]/templates[1]/t[1]/div[1]" position="attributes">
                <attribute name="color">lang</attribute>
              </xpath>
              <xpath expr="//form[1]/sheet[1]/notebook[1]/page[1]/field[@name='child_ids']/kanban[1]/templates[1]/t[1]/div[1]/field[@name='name']" position="after">
                <div class="o_dropdown_kanban dropdown" name="studio_div_302a40">
                  <a class="dropdown-toggle btn" data-toggle="dropdown" href="#">
                    <span class="fa fa-bars fa-lg"/>
                  </a>
                  <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel" name="studio_ul_4e2ccd">
                    <t t-if="widget.editable">
                      <li name="studio_li_ff8328">
                        <a type="edit">Edit</a>
                      </li>
                    </t>
                    <t t-if="widget.deletable">
                      <li name="studio_li_277a32">
                        <a type="delete">Delete</a>
                      </li>
                    </t>
                    <li name="studio_li_4f9d39">
                      <ul class="oe_kanban_colorpicker" data-field="lang" name="studio_ul_857488"/>
                    </li>
                  </ul>
                </div>
              </xpath>
            </data>
        """)

    # Correctly calculate the expr on flat views
    def test_view_normalization_23(self):
        self._test_view_normalization("""
            <data>
              <xpath expr="//gantt[1]" position="attributes">
                <attribute name="date_stop">date</attribute>
              </xpath>
            </data>
            """, """
            <data>
              <xpath expr="//gantt[1]" position="attributes">
                <attribute name="date_stop">date</attribute>
              </xpath>
            </data>
            """, 'gantt'
        )

    # test that unnamed groups/pages are given a pseudo-random name attribute
    def test_view_normalization_24(self):
        random.seed("https://i.redd.it/pnyr50lf0jh01.png")
        self._test_view_normalization("""
            <data>
                <xpath expr="//form[1]/sheet[1]/notebook[1]" position="after">
                  <group>
                    <p>hello world!</p>
                  </group>
                  <group>
                    <p>foo bar baz</p>
                  </group>
                  <group>
                    <p>spam eggs bacon</p>
                  </group>
                </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]" position="after">
                <group name="studio_group_a9eb51">
                  <p>hello world!</p>
                </group>
                <group name="studio_group_70d54a">
                  <p>foo bar baz</p>
                </group>
                <group name="studio_group_71063a">
                  <p>spam eggs bacon</p>
                </group>
              </xpath>
            </data>
        """)
        random.seed()

    # test that unnamed pages are given a pseudo-random name attribute
    def test_view_normalization_25(self):
        self._test_view_normalization("""
            <data>
                <xpath expr="//form[1]/sheet[1]/notebook[1]" position="inside">
                  <page>
                    <p>hello world!</p>
                  </page>
                  <page>
                    <p>foo bar baz</p>
                  </page>
                  <page>
                    <p>spam eggs bacon</p>
                  </page>
                </xpath>
            </data>
        """, """
            <data>
              <xpath expr="//form[1]/sheet[1]/notebook[1]" position="inside">
                <page name="studio_page_302a40">
                  <p>hello world!</p>
                </page>
                <page name="studio_page_4e2ccd">
                  <p>foo bar baz</p>
                </page>
                <page name="studio_page_ff8328">
                  <p>spam eggs bacon</p>
                </page>
              </xpath>
            </data>
        """)

    # Adjacent addition/removal changes ends with correct xpath
    def test_view_normalization_26(self):
        self._test_view_normalization("""
            <data>
              <field name="category_id" position="attributes">
                <attribute name="placeholder" />
                <attribute name="widget" />
              </field>
              <field name="category_id" position="after">
                <field name="create_uid"/>
              </field>
            </data>
        """, """
            <data>
              <xpath expr="//field[@name='category_id']" position="attributes">
                <attribute name="placeholder"/>
                <attribute name="widget"/>
              </xpath>
              <xpath expr="//field[@name='category_id']" position="after">
                <field name="create_uid"/>
              </xpath>
            </data>
        """)

    # Test descendants equivalent nodes does not change children
    def test_view_normalization_27(self):
        self._test_view_normalization("""
            <data>
              <field name="website" position="after">
                <div>
                    <field name="create_uid"/>
                </div>
                <div>
                    <field name="write_uid"/>
                </div>
              </field>
            </data>
        """, """
            <data>
              <xpath expr="//field[@name='website']" position="after">
                <div name="studio_div_302a40">
                  <field name="create_uid"/>
                </div>
                <div name="studio_div_4e2ccd">
                  <field name="write_uid"/>
                </div>
              </xpath>
            </data>
        """)

    # Test descendants equivalent nodes does not change children with unwrapped field
    def test_view_normalization_28(self):
        self._test_view_normalization("""
            <data>
              <field name="website" position="after">
                <div>
                    <div>
                    <field name="create_uid"/>
                    </div>
                    <field name="write_uid"/>
                </div>
              </field>
            </data>
        """, """
            <data>
              <xpath expr="//field[@name='website']" position="after">
                <div name="studio_div_302a40">
                  <div name="studio_div_4e2ccd">
                    <field name="create_uid"/>
                  </div>
                  <field name="write_uid"/>
                </div>
              </xpath>
            </data>
        """)

    def test_view_normalization_29(self):
        self.view = self.base_view.create({
            'arch_base':
            '''
              <form string="Partner">
                <sheet>
                  <div class="oe_title">
                    <h1>
                        <field name="name" />
                    </h1>
                  </div>
                </sheet>
              </form>
            ''',
            'model': 'res.partner',
            'type': 'form'})

        self._test_view_normalization(
            '''
              <data>
                <xpath expr="//sheet/*[1]" position="before">
                  <div class="oe_button_box" name="button_box">
                  </div>
                </xpath>
              </data>
            ''',
            '''
               <data>
                <xpath expr="//form[1]/sheet[1]/div[1]" position="before">
                  <div class="oe_button_box" name="button_box">
                  </div>
                </xpath>
              </data>
            ''')

    def test_view_normalization_30(self):
        self.view = self.base_view.create({
            'arch_base':
            '''
              <form string="Partner">
                <sheet>
                  <div class="oe_title">
                    <h1>
                        <field name="name" />
                    </h1>
                  </div>
                </sheet>
              </form>
            ''',
            'model': 'res.partner',
            'type': 'form'})

        self._test_view_normalization(
            '''
              <data>
                <xpath expr="//sheet/*[1]" position="before">
                  <div name="x_path_1"></div>
                </xpath>
                <xpath expr="//sheet/*[1]" position="before">
                  <div name="x_path_2"></div>
                </xpath>
              </data>
            ''',
            '''
               <data>
                <xpath expr="//form[1]/sheet[1]/div[1]" position="before">
                  <div name="x_path_2"/>
                  <div name="x_path_1"/>
                </xpath>
              </data>
            ''')

    def test_view_normalization_31(self):
        self.view = self.base_view.create({
            'arch_base':
            '''
              <form string="Partner">
                <sheet>
                  <div class="oe_title">
                    <h1>
                        <field name="name" />
                    </h1>
                  </div>
                  <div class="other_div">
                  </div>
                </sheet>
              </form>
            ''',
            'model': 'res.partner',
            'type': 'form'})

        # x_path_[1-3] target <div class="oe_title"/>
        # x_path_4 targets <div class="other_div"/>
        self._test_view_normalization(
            '''
              <data>
                <xpath expr="//sheet/*[1]" position="before">
                  <div name="x_path_1"></div>
                </xpath>
                <xpath expr="//sheet/*[2]" position="before">
                  <div name="x_path_2"></div>
                </xpath>
                <xpath expr="//sheet/*[4]" position="before">
                  <div name="x_path_3"></div>
                </xpath>
                <xpath expr="//sheet/*[5]" position="after">
                  <div name="x_path_4"></div>
                </xpath>
              </data>
            ''',
            '''
               <data>
                <xpath expr="//form[1]/sheet[1]/div[1]" position="before">
                  <div name="x_path_1"/>
                  <div name="x_path_2"/>
                </xpath>
                <xpath expr="//form[1]/sheet[1]/div[1]" position="after">
                  <div name="x_path_3"/>
                </xpath>
                <xpath expr="//form[1]/sheet[1]/div[2]" position="after">
                  <div name="x_path_4"/>
                </xpath>
              </data>
            ''')

    def tearDown(self):
        super(TestViewNormalization, self).tearDown()
        random.seed()
        _request_stack.pop()
