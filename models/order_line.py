# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class OrderLine(models.Model):
    _name = 'amgl.order_line'
    _description = 'Order Lines'

    @api.multi
    @api.depends('temp_received_quantity')
    def _calculate_received_remaining(self):
        received_weight = remaining_qty = remaining_weight = received_quantity = 0
        total_received = 0
        temp_received_weight = 0
        for order_lines in self:
            for order_line in order_lines:
                if order_line.temp_received_quantity > 0:
                    total_received = order_line.temp_received_quantity + order_line.total_received_quantity
                else:
                    total_received = order_line.total_received_quantity
                if order_line.order_id.is_deposit is True:
                    order_line.update({
                        'received_weight': order_line.total_weight,
                        'received_quantity': float(order_line.quantity),
                        'remaining_quantity': 0,
                        'remaining_weight': 0
                    })
                else:
                    for product in order_line.products:
                        if product.weight_unit == 'oz':
                            received_weight = product.weight_per_piece * total_received
                            remaining_qty = float(order_line.quantity) - total_received
                            remaining_weight = product.weight_per_piece * remaining_qty
                            temp_received_weight = product.weight_per_piece * order_line.temp_received_quantity
                        if product.weight_unit == 'gram':
                            received_weight = (product.weight_per_piece / 28.34952) * total_received
                            remaining_qty = float(order_line.quantity) - total_received
                            remaining_weight = product.weight_per_piece * remaining_qty
                            temp_received_weight = (product.weight_per_piece / 28.34952) * order_line.temp_received_quantity
                        if product.weight_unit == 'kg':
                            received_weight = (product.weight_per_piece / 0.02834952) * total_received
                            remaining_qty = float(order_line.quantity) - total_received
                            remaining_weight = (product.weight_per_piece / 0.02834952) * remaining_qty
                            temp_received_weight = product.weight_per_piece * order_line.temp_received_quantity
                        if product.weight_unit == 'pounds':
                            received_weight = (product.weight_per_piece * 16) * total_received
                            remaining_qty = float(order_line.quantity) - total_received
                            remaining_weight = product.weight_per_piece * remaining_qty
                            temp_received_weight = (product.weight_per_piece * 16) * order_line.temp_received_quantity
                    order_line.update({
                        'received_weight': received_weight,
                        'received_quantity': total_received,
                        'remaining_quantity': remaining_qty,
                        'remaining_weight': remaining_weight,
                        'temp_received_weight': temp_received_weight
                    })


    @api.multi
    @api.depends('products', 'quantity', 'weight')
    def _compute_total_weight_oz(self):
        total_weight = 0
        for order in self:
            qty = float(order.quantity)
            for product in order.products:
                if product.weight_unit == 'oz':
                    total_weight = qty * product.weight_per_piece
                if product.weight_unit == 'gram':
                    total_weight = qty * (product.weight_per_piece / 28.34952)
                if product.weight_unit == 'kg':
                    total_weight = qty * (product.weight_per_piece / 0.02834952)
                if product.weight_unit == 'pounds':
                    total_weight = qty * product.weight_per_piece * 16
            order.update({
                'total_weight': total_weight
            })

    @api.multi
    @api.depends('products', 'quantity')
    def _compute_weight_by_piece(self):
        total_weight = 0
        for order in self:
            for product in order.products:
                if product.weight_unit == 'oz':
                    total_weight = product.weight_per_piece
                if product.weight_unit == 'gram':
                    total_weight = product.weight_per_piece / 28.34952
                if product.weight_unit == 'kg':
                    total_weight = product.weight_per_piece / 0.02834952
                if product.weight_unit == 'pounds':
                    total_weight = product.weight_per_piece * 16
            order.update({
                'weight': total_weight
            })

    @api.multi
    @api.depends('products')
    def _get_commodity_from_product(self):
        for order_line in self:
            order_line.update({
                'commodity': order_line.products.type
            })

    @api.multi
    def write(self, vals):
        print self
        print vals.get('received_quantity')

    @api.model
    def default_get(self, fields):
        res = super(OrderLine, self).default_get(fields)
        return res

    name = fields.Char()
    products = fields.Many2one('amgl.products', string="Products", required=True)
    order_id = fields.Many2one('amgl.order', string='Orders')
    commodity = fields.Char(string="Commodity", readonly=True, compute="_get_commodity_from_product")
    customer_id = fields.Many2one('amgl.customer',related="order_id.customer_id",
                                  string="Customer Reference")
    metal_movement_id = fields.Many2one('amgl.metal_movement', string="Meta Movement Reference")
    total_received_quantity = fields.Float(string="Total Received Quantity")
    temp_received_quantity = fields.Float(string="Received Quantity", default=0)
    temp_received_weight = fields.Float(string="Received Weight", default=0, readonly=True)
    received_quantity = fields.Float(string='Received Quantity', compute='_calculate_received_remaining')
    received_weight = fields.Float(string='Received Weight', compute='_calculate_received_remaining')
    remaining_quantity = fields.Float(string='Remaining Quantity', compute='_calculate_received_remaining')
    remaining_weight = fields.Float(string='Remaining Weight', compute='_calculate_received_remaining')
    quantity = fields.Char(string="Quantity")
    weight = fields.Float(readonly=True, string="Weight", required=True, compute="_compute_weight_by_piece")
    total_weight = fields.Float(readonly=True, string="Total Weight",compute="_compute_total_weight_oz")
    customer_reference = fields.Many2one('amgl.customer',
                        related="metal_movement_id.customer", string="Customer Reference")
    is_deposit_related = fields.Boolean(default=False)
