from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PerformanceCPE(models.Model):
    _name = 'performance.cpe'
    _description = 'Continuous Performance Engagement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'cpe_date desc'

    def _default_employee(self):
        return self.env.user.id

    employee_id = fields.Many2one('res.users', string='Employee', required=True,
                                default=_default_employee, tracking=True)
    cpe_date = fields.Date(string='CPE Date', required=True,
                          default=fields.Date.today, tracking=True)
    accomplishments = fields.Text(string='Accomplishments', required=True,
                                tracking=True)
    challenges = fields.Text(string='Challenges', required=True, tracking=True)
    tasks = fields.Text(string='Tasks', required=True, tracking=True)
    overall_comment = fields.Text(string='Overall Comment', required=True,
                                tracking=True)
    employee_comment = fields.Text(string='Employee Comment', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted_by_manager', 'Submitted by Manager'),
        ('acknowledged_by_employee', 'Acknowledged by Employee')
    ], string='Status', default='draft', tracking=True)

    @api.constrains('cpe_date')
    def _check_cpe_date(self):
        for record in self:
            if record.cpe_date > fields.Date.today():
                raise ValidationError(_("CPE date cannot be in the future."))

    @api.constrains('accomplishments', 'challenges', 'tasks', 'overall_comment',
                   'employee_comment')
    def _check_text_fields(self):
        for record in self:
            # Check required fields are not empty
            for field, field_name in [
                (record.accomplishments, 'Accomplishments'),
                (record.challenges, 'Challenges'),
                (record.tasks, 'Tasks'),
                (record.overall_comment, 'Overall Comment')
            ]:
                if not field or not field.strip():
                    raise ValidationError(_(f"{field_name} cannot be empty."))

            # Check word count limits
            for field in [record.accomplishments, record.challenges,
                         record.tasks, record.overall_comment]:
                if len(field.split()) > 5000:
                    raise ValidationError(_("Text fields must not exceed 5000 words."))
            
            if record.employee_comment and len(record.employee_comment.split()) > 500:
                raise ValidationError(_("Employee comment must not exceed 500 words."))

    def action_submit_cpe(self):
        """Submit CPE by manager"""
        self.ensure_one()
        if not self.env.user.has_group('performance_reviews.group_manager'):
            raise ValidationError(_("Only managers can submit CPE."))
        
        self.state = 'submitted_by_manager'
        
        # Send email to employee
        template = self.env.ref('performance_reviews.email_template_cpe_submitted')
        template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('CPE has been submitted to the employee.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_acknowledge_cpe(self):
        """Employee acknowledges CPE"""
        self.ensure_one()
        if self.env.user != self.employee_id:
            raise ValidationError(_("Only the employee can acknowledge their CPE."))
        
        self.state = 'acknowledged_by_employee'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('CPE has been acknowledged.'),
                'type': 'success',
                'sticky': False,
            }
        }
