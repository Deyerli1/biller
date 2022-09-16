# -*- coding: utf-8 -*-
{

    'name': 'Biller all',

    'version': '1.0',

    'category': '',

    'summary': 'Modulo para instalar todos los modulos destinados a la integracion con Biller v2',

    'author': 'Jon Horton',

    'website': 'https://www.fiverr.com/horton_jon/set-up-customize-create-and-develop-odoo-erp-applications-for-you',

    'depends': [
        'account',
    ],

    'data': [

        'security/ir.model.access.csv',
        'wizard/get_documents_wizard_views.xml',
        'views/biller_record_views.xml',
        'views/account_move_view.xml',
        'views/product_template_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': """
Biller all
===========================
TO DO
""",

}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
