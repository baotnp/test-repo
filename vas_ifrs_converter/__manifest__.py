{
    'name': 'VAS to IFRS Real-time Converter',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Automatic real-time conversion from Vietnamese Accounting Standards (VAS) to International Financial Reporting Standards (IFRS)',
    'description': """
    VAS to IFRS Real-time Converter
    ===============================

    This module provides automatic real-time conversion between Vietnamese Accounting Standards (VAS) 
    and International Financial Reporting Standards (IFRS) in Odoo 18.

    Key Features:
    * Real-time conversion of journal entries
    * Dual reporting system (VAS + IFRS)
    * Automated mapping rules
    * Compliance reporting
    * Audit trail for all conversions
    * Multi-currency support
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': ['account', 'account_reports', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/vas_ifrs_mapping_data.xml',
        'views/vas_ifrs_mapping_views.xml',
        'views/account_move_views.xml',
        # 'views/ifrs_report_views.xml',
        'wizards/vas_ifrs_conversion_wizard_views.xml',
        'views/menu_views.xml',
        # 'reports/ifrs_financial_reports.xml',
    ],
    # 'demo': [
    #     'demo/demo_data.xml',
    # ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}