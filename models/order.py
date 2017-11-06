# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import logging

from lxml import etree

_logger = logging.getLogger(__name__)

class Order(models.Model):
    _name = 'amgl.order'
    _description = 'Order'

#region Order History Query & Data

    @staticmethod
    def _get_history_insert_query():
        query = """
                    INSERT INTO public.amgl_order_history(
                    create_uid, updated_by, order_id, write_uid, date_create, 
                    fields_updated, write_date, create_date, name)
                    VALUES ( %s, %s, %s, %s, %s, %s, now(), now(), '');"""
        return query

    @staticmethod
    def _get_history_insert_data(self,vals):
        user_id = self.env.user.id
        data = (1, user_id, self.ids.id, user_id, self.date_received, vals)
        return data

# endregion

#region Pending Order Query
    @staticmethod
    def _get_pending_order_query(self):
        return """
                SELECT c.name AS first_name,
                c.last_name AS last_name,
                o.related_total_received_qty AS quantity_received,
                o.total_qty AS quantity_expected
                FROM amgl_order AS o
                INNER JOIN amgl_customer AS c ON c.id = o.customer_id
                WHERE o.id ="""+str(self.ids[0])
#endregion

#region Pending Account Query

    @staticmethod
    def _get_pending_account_insert_query():
        return """
            INSERT INTO public.amgl_pending_accounts(
            create_uid, first_name, last_name, possible_solution, name, 
            notes, possible_reason, quantity_expected,
            write_uid, quantity_received, date_received, order_id)
            VALUES (%s, %s, %s, %s, %s,%s, %s, %s,%s, %s,now(), %s);"""

    @staticmethod
    def _get_pending_account_insert_data(self, vals):
        data = (self.env.user.id, self.customer_id.first_name, self.customer_id.last_name,
                1, '', '', 1, self.total_qty, self.env.user.id
                , vals.get('current_received_quantity'), self.ids[0])
        return data

#endregion

#region Default Class Methods

    @staticmethod
    def calculate_weight(product,quantity):
        total_weight = 0
        if product.weight_unit == 'oz':
            total_weight = quantity * product.weight_per_piece
        if product.weight_unit == 'gram':
            total_weight = quantity * (product.weight_per_piece / 28.34952)
        if product.weight_unit == 'kg':
            total_weight = quantity * (product.weight_per_piece / 0.02834952)
        if product.weight_unit == 'pounds':
            total_weight = quantity * product.weight_per_piece * 16
        return total_weight

    @api.multi
    @api.depends('order_line.products', 'order_line.quantity')
    def _compute_total_by_commodity(self):
        for order in self:
            total = gold = silver = platinum = palladium = 0
            total_weight = gold_weight = silver_weight = platinum_weight = palladium_weight = 0
            for line in self.order_line:
                for p in line.products:
                    qty = float(line.quantity)
                    if p['type'] == 'Gold':
                        gold += qty
                        total += qty
                        gold_weight += self.calculate_weight(p,qty)
                        total_weight += gold_weight
                    if p['type'] == 'Silver':
                        silver += qty
                        total += qty
                        silver_weight += self.calculate_weight(p, qty)
                        total_weight += silver_weight
                    if p['type'] == 'Platinum':
                        platinum += qty
                        total += qty
                        platinum_weight += self.calculate_weight(p, qty)
                        total_weight += platinum_weight
                    if p['type'] == 'Palladium':
                        palladium += qty
                        total += qty
                        palladium_weight += self.calculate_weight(p, qty)
                        total_weight += palladium_weight

            order.update({
                'total_by_commodity': total,
                'total_by_gold': gold,
                'total_by_silver': silver,
                'total_by_platinum': platinum,
                'total_by_palladium': palladium,
                'total_weight': total_weight,
                'gold_weight': gold_weight,
                'silver_weight': silver_weight,
                'platinum_weight': platinum_weight,
                'palladium_weight': palladium_weight,
                'total_weight_store': total_weight
            })

        return True

    @api.multi
    @api.depends('order_line.products', 'order_line.quantity')
    def _calculate_total_qty(self):
        for order in self:
            total = 0
            for line in order.order_line:
                for p in line.products:
                    total += float(line.quantity)

            order.update({
                'total_qty': total,
                'related_remaining_quantity': total
            })

        return True

    @api.model
    def create(self, vals):
        record = super(Order, self).create(vals)
        record['name'] = record['customer_id'].first_name + '-' + record['date_opened']
        record['state'] = 'expecting'
        if record['is_deposit'] is True:
            record['related_total_received_qty'] = record.order_line.temp_received_quantity
            record['related_remaining_quantity'] = 0
            record['state'] = 'completed'
            record.order_line.quantity = record.order_line.temp_received_quantity
            record['date_received'] = datetime.datetime.now()
            for single_order_line in record['order_line']:
                single_order_line.update({
                    'remaining_quantity': 0,
                    'remaining_weight': 0,
                    'received_quantity': float(single_order_line.quantity),
                    'received_weight': single_order_line.total_weight
                })
        return record

    def create_deposit(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

#region Write Method

    @api.multi
    def write(self, vals):
        if vals.get('current_received_quantity') is not None:
            current_received_amount, remaining_qty, total_received = self.remaining_received_local(vals)
            if self.env.user.has_group('amgl.group_amark_vault') and self.total_qty != current_received_amount:
                if (current_received_amount + self.related_total_received_qty) > self.total_qty\
                        or (current_received_amount + self.related_total_received_qty) < self.total_qty:
                    vals['is_pending'] = True
                    # Inserting Pending Account
                    self.env.cr.execute(self._get_pending_account_insert_query(),
                                        self._get_pending_account_insert_data(self, vals))

            if current_received_amount > 0.0:
                for order_line in self.order_line:
                    self.add_order_history(current_received_amount, remaining_qty, vals)
                    qty = float(order_line.quantity)
                    self.update_received_amount_to_order_line(current_received_amount, order_line, qty)
            if remaining_qty == 0:
                self.update_order_line_completed(total_received)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            else:
                self.update_order_line_state(remaining_qty, total_received)
        else:
            pass
        return super(Order, self).write(vals)

    def update_order_line_state(self, remaining_qty, total_received):
        self.env.cr.execute("""
                                Update amgl_order set is_pending = True,
                                state = 'pending',
                                related_remaining_quantity = """ + str(remaining_qty) + """,
                                related_total_received_qty = """ + str(total_received) + """
                                WHERE id = """ + str(self.ids[0]))

    def update_order_line_completed(self, total_received):
        self.env.cr.execute("""
                                    Update amgl_order set is_pending = False,
                                    state = 'completed',
                                    related_remaining_quantity = 0,
                                    related_total_received_qty = %s 
                                    WHERE id = %s""", [total_received, self.ids[0]])

    def update_received_amount_to_order_line(self, current_received_amount, order_line, qty):
        self.env.cr.execute("""
                                Update amgl_order_line
                               SET temp_received_quantity = %s,
                                total_received_quantity = %s 
                                WHERE id = %s""", [current_received_amount,
                                                   (order_line.total_received_quantity + current_received_amount),
                                                   self.ids[0]])

    def add_order_history(self, current_received_amount, remaining_qty, vals):
        self.env['amgl.order.history'].create(
            {'date_create': datetime.datetime.now(),
             'fields_updated': vals,
             'remaining_quantity': remaining_qty,
             'received_quantity': current_received_amount,
             'order_id': str(self.ids[0]),
             'updated_by': self.env.user.id})

    def remaining_received_local(self, vals):
        current_received_amount = float(vals.get('current_received_quantity'))
        total_received = current_received_amount + self.related_total_received_qty
        remaining_qty = self.total_qty - total_received
        return current_received_amount, remaining_qty, total_received

#endregion

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Order, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if (view_type == 'tree' or view_type == 'form') and self.env.user.has_group('amgl.group_amark_vault') and self.is_deposit is False:
            doc = etree.XML(res['arch'])
            for node_form in doc.xpath("//tree"):
                node_form.attrib['create'] = 'false'
                res['arch'] = etree.tostring(doc)
            for node_form in doc.xpath("//form"):
                node_form.attrib['create'] = 'false'
                res['arch'] = etree.tostring(doc)
        return res

#endregion

    @api.multi
    def open_wizard(self):
        return {
            'domain': "[('order_id','=', " + str(self.ids[0]) + ")]",
            "type": "ir.actions.act_window",
            "res_model": "amgl.order_line",
            "target": 'new',
            'flags': {'action_buttons': True},
            'view_mode': 'tree',
            "view_id": 352
        }

    name = fields.Char(string='Name',readonly=True)
    order_line = fields.One2many('amgl.order_line', 'order_id', string='Order Lines')
    related_products = fields.Many2one(related='order_line.products')
    current_received_quantity = fields.Float(string="Quantity Received", default=0.0, store=False)
    related_remaining_quantity = fields.Float(related='order_line.remaining_quantity', store=True)
    related_total_received_qty = fields.Float(related='order_line.total_received_quantity', store=True)
    is_vault_create_allowed = fields.Boolean(compute='_is_vault_create_allowed')
    order_history = fields.One2many('amgl.order.history', 'order_id', string='Order History Lines')
    total_qty = fields.Float(string='Total Expected',readonly=True,compute="_calculate_total_qty")
    customer_id = fields.Many2one('amgl.customer', string='Customer Name', readonly=True, required=True,default=lambda self: self._context.get('customer_id',False))
    account_number = fields.Char(string="Account Number", readonly=True, default=lambda self: self._context.get('account_number',False))
    date_opened = fields.Datetime('Date Opened', readonly=True, required=True, default=lambda self: self._context.get('date_opened',False))
    account_type = fields.Char(string="Account Type", readonly=True, default=lambda self: self._context.get('account_type', False))
    custodian_id = fields.Char(string="Custodian", readonly=True, default=lambda self: self._context.get('custodian_id', False))
    dealer_id = fields.Many2one('amgl.dealer',string="Dealer")
    is_pending = fields.Boolean()
    state = fields.Selection([('expecting', 'Expecting'), ('pending', 'Pending'),
                              ('completed', 'Completed'), ('waiting', 'Waiting For Approval')],
                             'Status', default='expecting', readonly=True,
                             help='Choose what is the current status of order')
    date_received = fields.Datetime('Date Received')
    total_by_commodity = fields.Float(string="Grand Total Pieces",compute="_compute_total_by_commodity")
    total_by_gold = fields.Float(string="Total Gold", compute="_compute_total_by_commodity")
    total_by_silver = fields.Float(string="Total Silver", compute="_compute_total_by_commodity")
    total_by_platinum = fields.Float(string="Total Platinum", compute="_compute_total_by_commodity")
    total_by_palladium = fields.Float(string="Total Palladium", compute="_compute_total_by_commodity")
    total_weight = fields.Float(string="Grand Total Weight", compute="_compute_total_by_commodity")
    total_weight_store = fields.Float(string="Grand Total Weight")
    gold_weight = fields.Float(string="Total Gold", compute="_compute_total_by_commodity")
    silver_weight = fields.Float(string="Total Silver", compute="_compute_total_by_commodity")
    platinum_weight = fields.Float(string="Total Platinum", compute="_compute_total_by_commodity")
    palladium_weight = fields.Float(string="Total Palladium", compute="_compute_total_by_commodity")
    is_deposit = fields.Boolean(string='Deposit', default=lambda self: self._context.get('is_deposit', False))
    show_footer = fields.Boolean(string='Show Footer', default=lambda self: self._context.get('show_footer', False))
