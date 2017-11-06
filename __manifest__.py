# -*- coding: utf-8 -*-
{
    'name': "AMGL",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ahsan A.",
    'website': "http://www.amark.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/amgl_security.xml',
        'views/views.xml',
        'views/customer.xml',
        'views/dashboard.xml',
        'views/custodian.xml',
        'views/products.xml',
        'views/order.xml',
        'views/order_line.xml',
        'views/metal_movement.xml',
        'views/possible_solutions.xml',
        'views/possible_reasons.xml',
        'views/pending_accounts.xml',
        'views/dealer.xml',
        'emailTemplates/mmr_create_mail.xml',
        'emailTemplates/reject_mmr_email.xml',
        'emailTemplates/mmr_approval_complete.xml',
        'emailTemplates/mmr_approve_reject_button.xml',
        'report/metal_movement_template.xml',
        'report/metal_movement_view.xml',
        'views/res_user.xml',
        'static/src/xml/extension_templates.xml'
    ],
    'qweb': [
        "views/colspan.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        'demo/customer_view.xml'
    ]
}