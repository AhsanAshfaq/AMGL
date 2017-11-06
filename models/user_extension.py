# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class UserExtension(models.Model):
    _name = 'amgl.user.extension'
    _inherit = 'res.users'

    x_custodian_id = fields.Many2one('amgl.custodian', string='Custodians')

    @api.model
    def create(self, values):
        user = super(UserExtension, self).create(values)
        return user