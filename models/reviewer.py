from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PerformanceReviewer(models.Model):
    _name = 'performance.reviewer'
    _description = 'Performance Review Reviewer'

    feedback_id = fields.Many2one('performance.feedback', string='Feedback',
                                required=True, ondelete='cascade')
    reviewer_id = fields.Many2one('res.users', string='Reviewer', required=True)
    relation_type = fields.Selection([
        ('director', 'Director'),
        ('hod', 'HOD'),
        ('colleagues', 'Colleagues'),
        ('cross_functional', 'Cross Functional Team')
    ], string='Relation Type', required=True)

    _sql_constraints = [
        ('unique_reviewer_per_feedback',
         'UNIQUE(feedback_id, reviewer_id)',
         'A reviewer can only be added once to a feedback form.')
    ]
