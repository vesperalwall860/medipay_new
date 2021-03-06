import re

from flask_wtf import Form
from flask import request
from werkzeug.utils import secure_filename
from wtforms import StringField, RadioField, SubmitField, TextAreaField
from wtforms import HiddenField, SelectField, FileField, ValidationError
from wtforms import PasswordField, SelectMultipleField, BooleanField
from wtforms import DateField, DateTimeField
from wtforms.validators import Required, Email, Length, EqualTo, URL
from flask_login import current_user

from ..models import Payer, Member, User, Provider


class BaseForm(Form):
    '''
    Base Class for all other form classes in the main section
    '''
    class Meta:
        '''
        Meta properties for binding fields for all oter form classes in the main section
        '''
        def bind_field(self, form, unbound_field, options):
            '''
            Removes trailing and leading spcaes from all fields submitted in form
            '''
            filters = unbound_field.kwargs.get('filters', [])
            filters.append(strip_filter)
            return unbound_field.bind(form=form, filters=filters, **options)

    def prepopulate(self, model, exclude=[]):
        """Prepopulates the form with a given model"""
        for col in model.columns():
            if col not in exclude and hasattr(self, col):
                setattr(getattr(self, col), 'data', getattr(model, col))


def strip_filter(value):
    '''
    removes leading and trailing white space
    '''
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value


def validate_email_address(form, field):
    '''
    validates email address
    '''
    if field.data:
        match = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"\
          ,field.data)
        if match == None:
            raise ValidationError('Invalid Email address.')

        if len(field.data) < 1 or len(field.data) > 64:
            raise ValidationError('Field must be between 1 and 64 ' + \
             'characters long.')


def validate_numeric(form, field):
    '''
    validates numeric data type on the input field
    '''
    if field.data:
        match = re.match(r"^[0-9]+$", field.data)
        if match == None:
            raise ValidationError('Only digits are allowed.')


def validate_phone(form, field):
    '''
    validates phone data type on the input field
    '''
    if field.data:
        match = re.match(r"^\+?[0-9]+$", field.data)
        if match == None:
            raise ValidationError('Invalid phone number.')


def validate_payer_email_address(form, field):
    '''
    checks if email address is already registered in the system or not
    '''
    if field.data:
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

        if Payer.query.filter_by(pic_email=field.data).first() or \
            Payer.query.filter_by(pic_alt_email=field.data).first():
            raise ValidationError('Email already registered.')


def validate_comma_sep_dec(form, field):
    '''
    removes comma and minus sign from fee input and stores the value if it is greater than 0
    '''
    field.data = field.data.replace(',' ,'').replace('-','')
    try:
        field.data = float(field.data)
        if field.data < 0:
            raise ValidationError('Fee cannot be less than 0')
    except ValueError:
        field.data = 0.0
        
def validate_empty_fee(form, field):
    '''
    validates empty fee field on the form
    '''
    try:
        field.data = float(field.data)
        if field.data < 0:
            raise ValidationError('Fee cannot be less than 0')
    except ValueError:
        field.data = 0.0


class GOPForm(BaseForm):
    '''
    GOP request form
    '''
    patient_medical_no = StringField('Patient medical no.',
                                     validators=[Required()])
    payer = SelectField('Payer Select', coerce=int, choices=[('0', 'None')])
    policy_number = StringField('Policy Number', validators=[Required()])
    name = StringField('Name', validators=[Required()])
    dob = DateField('Date of birth', validators=[Required()],
                    format='%d/%m/%Y')
    gender = RadioField('Sex', validators=[Required()],
                        choices=[('male', 'Male'), ('female', 'Female')])
    tel = StringField('Patient phone nr.', validators=[Required(),
                      validate_phone])

    current_national_id = HiddenField('Current national ID')

    patient_action_plan = TextAreaField('Plan of action',
                                        validators=[Required()])
    national_id = StringField('Patient ID', validators=[Required()])
    member_photo = FileField('Patient photo')
    medical_details_symptoms = StringField('Symptoms')
    medical_details_temperature = StringField('Temperature')
    medical_details_heart_rate = StringField('Heart rate')
    medical_details_respiration = StringField('Respiration')
    medical_details_blood_pressure = StringField('Blood pressure')
    medical_details_physical_finding = StringField('Physical finding')
    medical_details_health_history = TextAreaField('Health history')
    medical_details_previously_admitted = DateField('Previously admitted',
                                                    format='%d/%m/%Y')
    medical_details_diagnosis = StringField('Diagnosis')
    medical_details_in_patient = BooleanField('In patient indication')
    medical_details_test_results = TextAreaField('Test results')
    medical_details_current_therapy = StringField('Current therapy')
    medical_details_treatment_plan = TextAreaField('Treatment plan')

    doctor_name = SelectField('Doctor name', validators=[Required()],
                              coerce=int, choices=[('0', 'None')])
    admission_date = DateTimeField('Admission date', validators=[Required()],
                                                     format='%d/%m/%Y')
    admission_time = DateTimeField('Admission time', validators=[Required()],
                                                     format='%I:%M %p')

    icd_codes = SelectMultipleField('ICD codes', validators=[Required()],
                                    coerce=int)

    room_price = StringField('Room price', validators=[Required(), 
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee],
                                                       default='0')
    room_type = SelectField('Room type', validators=[Required()],
                            choices=[(False, 'SELECT ROOM'),
                                     ('na', 'NA'),
                                     ('i', 'I'),
                                     ('ii', 'II'),
                                     ('iii', 'III'),
                                     ('iv', 'IV'),
                                     ('vip', 'VIP')])

    reason = RadioField('Reason', validators=[Required()],
                        choices=[('general', 'General'),
                                 ('specialist', 'Specialist'),
                                 ('emergency', 'Emergency'),
                                 ('scheduled', 'Scheduled')])

    doctor_fee = StringField('Doctor fee', validators=[Required(),
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee],
                                                       default='0')
    surgery_fee = StringField('Surgery fee', validators=[Required(),
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee],
                                                       default='0')
    medication_fee = StringField('Medication fee', validators=[Required(),
                                                       validate_comma_sep_dec,
                                                       validate_empty_fee],
                                                       default='0')
    quotation = StringField('Quotation', validators=[Required(),
                                                     validate_comma_sep_dec,
                                                     validate_empty_fee],
                                                     default='0')
    submit = SubmitField('Submit')

    def validate_national_id(self, field):
        '''
        checks if the id of the patient is present in the system or not
        '''
        if field.data != self.current_national_id.data and \
          Member.query.filter_by(national_id=field.data).first():
            raise ValidationError('Patient ID already exists.')

    def validate_member_photo(self, field):
        '''
        validates the member image upload
        '''
        if field.data:
            filename = secure_filename(field.data.filename)
            allowed = ['jpg', 'jpeg', 'png', 'gif']
            if not ('.' in filename and filename.rsplit('.', 1)[1] in allowed):
              raise ValidationError("Only image files are allowed.")


class GOPApproveForm(BaseForm):
    '''
    GOP approval form
    '''
    status = HiddenField('Status')
    submit_approve = SubmitField('Approve')
    reason_decline = StringField('Reason decline')
    submit_decline = SubmitField('Decline')

    def validate_reason_decline(self, field):
        '''
        decine gop request field cannot be left empty
        '''
        if self.status.data == 'declined' and not len(field.data):
            raise ValidationError('The reason is required when declining.')
