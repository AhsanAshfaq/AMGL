# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from lxml import etree


class Customer(models.Model):
    _name = 'amgl.customer'
    _rec_name = 'full_name'
    _description = 'IRA Customer'
    _order = 'last_name,first_name, account_number asc'


    @api.multi
    def redirect_to_order(self):
        view_id = self.env.ref('amgl.order_form').id
        return {
            "type": "ir.actions.act_window",
            "res_model": "amgl.order",
            "views": [[view_id, "form"]],
            "context": {'customer_id': self.id,
                        'account_number': self.account_number,
                        'date_opened': self.date_opened,
                        'custodian_id': self.custodian_id.name,
                        'account_type': self.account_type}
        }

    def custom_domain_function(self, cr, uid, context=None):
        print self

    @api.multi
    def _compile_fullname(self):
        for customer in self:
            first_name = ''
            if customer.first_name is False:
                first_name = customer.name
            else:
                first_name = customer.first_name

            fullname = first_name + ' ' + customer.last_name

            customer.update({
                'full_name': fullname,
                'first_name': first_name
            })

    @api.multi
    def _get_number_of_orders(self):
        number_of_records = 0
        for customer in self:
            for order in customer.customer_orders:
                number_of_records += 1
            customer.update({
                'number_of_orders': number_of_records
            })

    @api.multi
    def _calculate_existing_inventory(self):
        total_gold = total_silver = total_platinum = total_palladium = total = 0
        for customer in self:
            for order in customer.customer_orders:
                if order.state == 'completed':
                    for line in order.order_line:
                        qty = float(line.quantity)
                        for p in line.products:
                            if p['type'] == 'Gold':
                                total_gold += qty
                                total += qty
                            if p['type'] == 'Silver':
                                total_silver += qty
                                total += qty
                            if p['type'] == 'Platinum':
                                total_platinum += qty
                                total += qty
                            if p['type'] == 'Palladium':
                                total_palladium += qty
                                total += qty
        customer.update({
            'total_gold': total_gold,
            'total_silver': total_silver,
            'total_platinum': total_platinum,
            'total_palladium': total_palladium,
            'total': total
        })

    @api.multi
    def _calculate_deposit_inventory(self):
        is_custodian_readonly = False
        if self.env.user.has_group('amgl.group_amark_custodian'):
            is_custodian_readonly = True

        total_gold = total_silver = total_platinum = total_palladium = total = 0
        for customer in self:
            for inventory in customer.inventories:
                if inventory.products.type == 'Gold':
                    total_gold += inventory.quantity
                    total += inventory.quantity
                if inventory.products.type == 'Silver':
                    total_silver += inventory.quantity
                    total += inventory.quantity
                if inventory.products.type == 'Platinum':
                    total_platinum += inventory.quantity
                    total += inventory.quantity
                if inventory.products.type == 'Palladium':
                    total_palladium += inventory.quantity
                    total += inventory.quantity
        customer.update({
            'total_gold_deposit': total_gold,
            'total_silver_deposit': total_silver,
            'total_platinum_deposit': total_platinum,
            'total_palladium_deposit': total_palladium,
            'total_deposit': total,
            'readonly_custodian': is_custodian_readonly
        })

    @api.multi
    def add_deposit_action(self):
        view_id = self.env.ref('amgl.order_deposit_form').id
        return {
            "type": "ir.actions.act_window",
            "name": 'Add A Deposit',
            "res_model": "amgl.order",
            "views": [[view_id, "form"]],
            "context": {'customer_id': self.id,
                        'account_number': self.account_number,
                        'date_opened': self.date_opened,
                        'account_type': self.account_type,
                        'custodian_id':self.custodian_id.name,
                        'is_deposit': True,
                        'show_footer': True
                        },
            'target': 'new',
        }

    @api.model
    def default_get(self, fields):
        res = super(Customer, self).default_get(fields)
        res['custodian_id'] = self.env.user.x_custodian_id.id
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Customer, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        for node_form in doc.xpath("//tree"):
            node_form.attrib['duplicate'] = '0'
            res['arch'] = etree.tostring(doc)
        for node_form in doc.xpath("//form"):
            node_form.attrib['duplicate'] = '0'
            res['arch'] = etree.tostring(doc)
        return res

    first_name = fields.Char('First Name', required=True)
    last_name = fields.Char('Last Name', required=True)
    account_number = fields.Char('Account Number', required=True)
    date_opened = fields.Date('Date Opened', required=True)
    readonly_custodian = fields.Boolean(default=lambda self: self.env.user.has_group('amgl.group_amark_custodian'))
    full_name = fields.Char(string="Full Name", compute="_compile_fullname")
    user_id = fields.Integer(default=
                             lambda self: self.env.user.id
                             if (self.env.user.partner_id.parent_id is False)
                             else self.env.user.partner_id.parent_id.id - 1)
    account_type = fields.Selection(selection=[('Commingled', 'Commingled'),
                                               ('Segregated', 'Segregated')])
    customer_orders = fields.One2many('amgl.order', 'customer_id',
                                      domain=[('state', '!=', 'completed')],
                                      string='Inventories Against User')
    customer_orders_2 = fields.One2many('amgl.order', 'customer_id',
                                        domain=[('state', '=', 'completed')])
    product_ids = fields.Many2many('amgl.products', string='Products')
    custodian_id = fields.Many2one('amgl.custodian', string="Custodian", domain=[('groups_id', 'in', [12])],
                                 readonly=[('readonly_custodian', '=', ['groups_id', 'in', [12]])])
    dealer_ids = fields.Many2many('amgl.dealer', string='Dealers')
    number_of_orders = fields.Integer(string="Number Of Orders", compute="_get_number_of_orders")
    total_gold = fields.Float(string='Total Gold', compute='_calculate_existing_inventory')
    total_silver = fields.Float(string='Total Silver', compute='_calculate_existing_inventory')
    total_platinum = fields.Float(string='Total Platinum', compute='_calculate_existing_inventory')
    total_palladium = fields.Float(string='Total Palladium', compute='_calculate_existing_inventory')
    total = fields.Float(string='Grand Total', compute='_calculate_existing_inventory')
    total_gold_deposit = fields.Float(string='Total Gold', compute='_calculate_deposit_inventory')
    total_silver_deposit = fields.Float(string='Total Silver', compute='_calculate_deposit_inventory')
    total_platinum_deposit = fields.Float(string='Total Platinum', compute='_calculate_deposit_inventory')
    total_palladium_deposit = fields.Float(string='Total Palladium', compute='_calculate_deposit_inventory')
    total_deposit = fields.Float(string='Grand Total', compute='_calculate_deposit_inventory')
    inventories = fields.One2many('amgl.inventory', 'customer_id', string='Add Deposit')
    show_deposit = fields.Boolean(string='Show Deposit', default=True)
