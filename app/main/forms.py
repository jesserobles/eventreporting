from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField, SelectField, ValidationError, \
    SelectMultipleField, DateField, IntegerField, widgets, FormField, Form
from flask_pagedown.fields import PageDownField
from wtforms.validators import DataRequired, Length, Email, Regexp, NumberRange, InputRequired, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms_alchemy import ModelFieldList, ModelForm
from ..models import Role, User, Facility, CFR, System, EIISComponentType, Component, ComponentCause, Manufacturer


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class EditProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(0, 64)])
    last_name = StringField('Last Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                          'Usernames must have only letters, numbers, dots,'
                                                          ' or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    first_name = StringField('First Name', validators=[Length(0, 64)])
    last_name = StringField('Last Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


def get_cfrs():
    return CFR.query.all()


class CFRSelectForm(FlaskForm):
    cfr = QuerySelectField(query_factory=get_cfrs)


class AddComponentForm(ModelForm):
    system = SelectField("System", coerce=int)
    component_type = SelectField("Component Type", coerce=int)
    manufacturer = SelectField("Manufacturer", coerce=int)#StringField("Manufacturer")
    cause = SelectField("Failure Cause", coerce=int)
    reportable_ices = BooleanField("Reportable to ICES")
    inpo_device_id = StringField("INPO Device ID")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.system.choices = [(system.id, '{} ({})'.format(system.name, system.eiis_code))
                               for system in System.query.order_by(System.name).all()]
        self.system.choices.insert(0, (-1,''))
        self.component_type.choices = [(componenttype.id, '{} ({})'.format(componenttype.name, componenttype.eiis_code))
                                       for componenttype in
                                       EIISComponentType.query.order_by(EIISComponentType.name).all()]
        self.component_type.choices.insert(0, (-1, ''))
        self.manufacturer.choices = [(man.id, man.name) for man in Manufacturer.query.order_by(Manufacturer.name).all()]
        self.manufacturer.choices.insert(0, (-1, ''))
        self.cause.choices = [(cause.id, cause.cause_name) for cause in ComponentCause.query.all()]
        self.cause.choices.insert(0, (-1, ''))


class LERForm(FlaskForm):
    facilities = SelectMultipleField("Select Facilities", coerce=int, validators=[DataRequired()],
                                     render_kw={'data-placeholder':"Select affected facilities..."})
    title = StringField('Title', validators=[Length(0, 200), DataRequired()],
                        render_kw={"placeholder": "Up to 200 characters"})
    event_date = DateField('Event Date', validators=[DataRequired()], format="%m/%d/%Y",
                           render_kw={"placeholder": "mm/dd/yyyy"})
    operating_mode = SelectField('Operating Mode', validators=[DataRequired()])
    power_level = IntegerField('Power Level', render_kw={"placeholder": "e.g., 100"}, validators=[InputRequired(),
                                                                                                  NumberRange(min=0,
                                                                                                              max=100,
                                                                                                              )])
    cfrs = SelectMultipleField("Report Submitted Pursuant to Requirements of 10 CFR: (Select all that apply)",
                               coerce=int, validators=[DataRequired()],
                               render_kw={'data-placeholder': "Select all that apply..."})
    components = ModelFieldList(FormField(AddComponentForm), min_entries=1)
    supplement_expected = BooleanField("Supplemental Report Expected")
    supplement_date = DateField("Expected Supplement Submission Date", format="%m/%d/%Y",
                                validators=[Optional()],
                                render_kw={"placeholder": "mm/dd/yyyy"})
    abstract = TextAreaField("Abstract", validators=[DataRequired()])
    body = PageDownField("LER Text", validators=[DataRequired()])
    submit = SubmitField('Create LER')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facilities.choices = [(docket.id, '{} - {}'.format(docket.docket, docket.facility_name))
                                   for docket in Facility.query.order_by(Facility.facility_name).all()
                                   if docket.docket.startswith('050')]
        self.cfrs.choices = [(cfr.id, cfr.cfr) for cfr in CFR.query.order_by(CFR.cfr).all()]
        self.operating_mode.choices = [('N/A', 'N/A'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]