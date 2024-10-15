# -*- coding: utf-8 -*-
{
    'name': 'Web Notification',
    'version': '15.0.1.0',
    'author': 'Intech Creative Services Pvt. Ltd.',
    'company': 'Intech Creative Services Pvt. Ltd.',
    'category': 'Base',
    'summary': 'Web Notification',
    'license': 'Other proprietary',
    'description': """ Web Notification.""",
    'depends': ['freight_base'],
    'data': [
        'data/web_notification_cron.xml',
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/notification_settings_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'web_notification/static/src/js/notification_service.js',
        ],
    },
    'installable': True,
    'application': False
}
