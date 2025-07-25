{
    'name': 'Performance Reviews',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Performance Reviews Management System',
    'description': """
        This module provides a comprehensive performance review system with:
        - Roles, Responsibilities and Expectations (RRE)
        - Continuous Performance Engagement (CPE)
        - 360° Feedback System
    """,
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/rre_views.xml',
        'views/cpe_views.xml',
        'views/feedback_views.xml',
        'views/hr_dashboard_views.xml',
        'data/mail_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'icon': 'performance_reviews/static/description/icon.png',
    'web_icon': 'performance_reviews,static/description/icon.png',
    'assets': {
        'web.assets_backend': [
            'performance_reviews/static/src/scss/performance_reviews.scss',
            'performance_reviews/static/src/scss/app.scss',
            'performance_reviews/static/src/img/menu_icon.png',
        ],
    },
}
