from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PerformanceFeedback(models.Model):
    _name = 'performance.feedback'
    _description = '360 Degree Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee(self):
        return self.env.user.id

    employee_id = fields.Many2one('res.users', string='Employee', required=True,
                                default=_default_employee, tracking=True)
    manager_id = fields.Many2one('res.users', string='Manager', tracking=True)
    feedback_date = fields.Date(string='Feedback Date', required=True,
                              default=fields.Date.today, tracking=True)
    reviewers = fields.One2many('performance.reviewer', 'feedback_id',
                               string='Reviewers')
    request_details = fields.Text(string='Request Details', tracking=True)
    technical_performance = fields.Text(string='Technical Performance', tracking=True)
    interpersonal_skills = fields.Text(string='Interpersonal Skills', tracking=True)
    leadership_skills = fields.Text(string='Leadership Skills', tracking=True)
    strengths = fields.Text(string='Strengths', tracking=True)
    areas_for_improvement = fields.Text(string='Areas for Improvement', tracking=True)
    overall_feedback = fields.Text(string='Overall Feedback', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)

    @api.constrains('reviewers')
    def _check_reviewers(self):
        for record in self:
            if record.state != 'draft' and len(record.reviewers) < 4:
                raise ValidationError(_("At least 4 reviewers are required."))
            if len(record.reviewers) > 6:
                raise ValidationError(_("Maximum 6 reviewers are allowed."))

            # Check for required relation types
            relation_types = record.reviewers.mapped('relation_type')
            required_types = {'director', 'hod', 'colleagues', 'cross_functional'}
            missing_types = required_types - set(relation_types)
            
            if record.state != 'draft' and missing_types:
                raise ValidationError(
                    _("Missing reviewers from the following categories: %s") %
                    ', '.join(missing_types))
                
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Set the manager when employee changes"""
        if self.employee_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.employee_id.id)], limit=1)
            if employee and employee.parent_id and employee.parent_id.user_id:
                self.manager_id = employee.parent_id.user_id.id

    @api.constrains('request_details', 'technical_performance', 'interpersonal_skills',
                   'leadership_skills', 'strengths', 'areas_for_improvement', 'overall_feedback')
    def _check_text_fields(self):
        for record in self:
            # For submission, check request_details is provided
            if record.state != 'draft' and (not record.request_details or not record.request_details.strip()):
                raise ValidationError(_("Request details are required."))
                
            # For completed state, check manager feedback fields
            if record.state == 'completed':
                required_fields = [
                    (record.technical_performance, 'Technical Performance'),
                    (record.interpersonal_skills, 'Interpersonal Skills'),
                    (record.leadership_skills, 'Leadership Skills'),
                    (record.strengths, 'Strengths'),
                    (record.areas_for_improvement, 'Areas for Improvement'),
                    (record.overall_feedback, 'Overall Feedback')
                ]
                for field_value, field_name in required_fields:
                    if not field_value or not field_value.strip():
                        raise ValidationError(_(f"{field_name} is required."))
            
            # Check word counts
            if record.request_details and len(record.request_details.split()) > 500:
                raise ValidationError(_("Request details must not exceed 500 words."))
                
            for field in [record.technical_performance, record.interpersonal_skills, 
                         record.leadership_skills, record.strengths, 
                         record.areas_for_improvement, record.overall_feedback]:
                if field and len(field.split()) > 500:
                    raise ValidationError(_("Feedback fields must not exceed 500 words."))

    def action_submit_request(self):
        """Submit 360° feedback request"""
        self.ensure_one()
        if self.env.user != self.employee_id:
            raise ValidationError(_("Only the employee can submit their feedback request."))
        
        if len(self.reviewers) < 4:
            raise ValidationError(_("At least 4 reviewers are required."))
            
        # Check for required relation types
        relation_types = self.reviewers.mapped('relation_type')
        required_types = {'director', 'hod', 'colleagues', 'cross_functional'}
        missing_types = required_types - set(relation_types)
        
        if missing_types:
            raise ValidationError(
                _("Missing reviewers from the following categories: %s") %
                ', '.join(missing_types))
                
        if not self.request_details or not self.request_details.strip():
            raise ValidationError(_("Please provide request details."))
        
        self.state = 'in_progress'
        
        # Send email to manager and employee
        template = self.env.ref('performance_reviews.email_template_feedback_submitted')
        template.send_mail(self.id, force_send=True)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('360° feedback request has been submitted.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'effect',
                    'effects': {
                        'type': 'rainbow_man',
                        'message': _('Well done! Your 360° feedback request has been submitted!'),
                    }
                }
            }
        }

    def action_complete_feedback(self):
        """Complete 360° feedback with manager input"""
        self.ensure_one()
        if not self.manager_id:
            raise ValidationError(_("No manager assigned to this feedback."))
            
        if self.env.user.id != self.manager_id.id and not self.env.user.has_group('performance_reviews.group_hr_manager'):
            raise ValidationError(_("Only the assigned manager or HR managers can complete feedback."))
        
        # Check all required feedback fields
        required_fields = [
            (self.technical_performance, 'Technical Performance'),
            (self.interpersonal_skills, 'Interpersonal Skills'),
            (self.leadership_skills, 'Leadership Skills'),
            (self.strengths, 'Strengths'),
            (self.areas_for_improvement, 'Areas for Improvement'),
            (self.overall_feedback, 'Overall Feedback')
        ]
        for field_value, field_name in required_fields:
            if not field_value or not field_value.strip():
                raise ValidationError(_(f"{field_name} is required."))
        
        self.state = 'completed'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('360° feedback has been completed.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'effect',
                    'effects': {
                        'type': 'rainbow_man',
                        'message': _('Great job! The 360° feedback has been completed successfully!'),
                    }
                }
            }
        }
        
    def action_reset_to_draft(self):
        """Reset 360° Feedback to draft state (HR Manager only)"""
        self.ensure_one()
        if not self.env.user.has_group('performance_reviews.group_hr_manager'):
            raise ValidationError(_("Only HR Managers can reset feedback to draft."))
        
        self.state = 'draft'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reset Successful'),
                'message': _('360° Feedback has been reset to draft state.'),
                'type': 'success',
                'sticky': False,
            }
        }
