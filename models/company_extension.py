# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class CompanyExtension(models.Model):
    _name = 'amgl.company.extension'
    _inherit = 'res.company'

@api.model
def create(self, values):
    return super(CompanyExtension, self).create(values)