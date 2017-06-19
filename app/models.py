from datetime import datetime
import csv
import hashlib
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from . import db
from . import login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Permission:
    READ = 0x01
    WRITE = 0x02
    APPROVE = 0x04
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.READ, True),
            'Author': (Permission.READ |
                       Permission.WRITE, False),
            'Approver': (Permission.READ |
                         Permission.WRITE |
                         Permission.APPROVE, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    # phone = db.Column(db.Integer)
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    # facilities = db.relationship('Facility', backref='author')
    lers = db.relationship('LER', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['NRCEVENTS_ADMIN']:
                self.confirmed = True
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=60*60*48):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=60*60*48):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=60*60*48):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default,
                                                                     rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     first_name=forgery_py.name.first_name(),
                     last_name=forgery_py.name.last_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


class Facility(db.Model):
    __tablename__ = 'facilities'
    id = db.Column(db.Integer, primary_key=True)
    docket = db.Column(db.String, index=True)
    facility_name = db.Column(db.String)
    facility_type = db.Column(db.String)
    components = db.relationship('Component', backref='facility', lazy='dynamic')

    def __repr__(self):
        return '<Facility %r>' % self.facility_name

    @staticmethod
    def insert_facilities():
        with open('data/dockets', 'r') as file:
            reader = csv.reader(file)
            for r in reader:
                docket, name, ftype = r
                fac = Facility.query.filter_by(docket=docket).first()
                if fac is None:
                    fac = Facility(docket=docket, facility_name=name, facility_type=ftype)
                db.session.add(fac)
        db.session.commit()


class CFR(db.Model):
    __tablename__ = 'cfrcodes'
    id = db.Column(db.Integer, primary_key=True)
    cfr = db.Column(db.String(64), index=True)

    def __repr__(self):
        return '<CFR %r>' % self.cfr

    @staticmethod
    def insert_cfrs():
        with open('data/cfrs', 'r') as file:
            reader = csv.reader(file)
            codes = [line[0].strip() for line in reader]
            # codes = [line.strip() for line in file]
        for c in codes:
            cfr = CFR.query.filter_by(cfr=c).first()
            if cfr is None:
                cfr = CFR(cfr=c)
            db.session.add(cfr)
        db.session.commit()


cfrselected = db.Table('cfrselected',
                       db.Column('ler_id', db.Integer, db.ForeignKey('lers.id')),
                       db.Column('cfr_id', db.Integer, db.ForeignKey('cfrcodes.id'))
)

facilitiesinvolved = db.Table('facilitiesinvolved',
                              db.Column('ler_id', db.Integer, db.ForeignKey('lers.id')),
                              db.Column('facility_id', db.Integer, db.ForeignKey('facilities.id'))
)


class EIISComponentType(db.Model):
    __tablename__ = 'eiiscomponenttypes'
    id = db.Column(db.Integer, primary_key=True)
    eiis_code = db.Column(db.String(6))
    name = db.Column(db.String(100))
    components = db.relationship('Component', backref='eiiscomponenttype', lazy='dynamic')

    def __repr__(self):
        return '<EIISComponentType(%r, %r)>' % (self.eiis_code, self.name)

    @staticmethod
    def insert_eiiscomponenttypes():
        with open('data/eiis', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                code, name = row
                component = EIISComponentType.query.filter_by(eiis_code=code).first()
                if component is None:
                    component = EIISComponentType(eiis_code=code, name=name)
                    db.session.add(component)
            db.session.commit()


class System(db.Model):
    __tablename__ = 'systems'
    id = db.Column(db.Integer, primary_key=True)
    eiis_code = db.Column(db.String(4), index=True)
    name = db.Column(db.String(100))
    components = db.relationship('Component', backref='system', lazy='dynamic')

    def __repr__(self):
        return '<System %r>' % self.name

    @staticmethod
    def insert_systems():
        with open('data/systems', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                code, name = row
                system = System.query.filter_by(eiis_code=code).first()
                if system is None:
                    system = System(eiis_code=code, name=name)
                    db.session.add(system)
            db.session.commit()


class Component(db.Model):
    __tablename__ = 'components'
    id = db.Column(db.Integer, primary_key=True)
    system_id = db.Column(db.Integer, db.ForeignKey('systems.id'))
    eiiscomponenttype_id = db.Column(db.Integer, db.ForeignKey('eiiscomponenttypes.id'))
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'))
    inpo_device_id = db.Column(db.Integer)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'))
    lers = db.relationship("ComponentFailure", backref="component", lazy='dynamic')

    def __repr__(self):
        return '<Component(%r, %r, %r, %r, %r)>' % (self.id, self.facility_id, self.eiiscomponenttype_id, self.system_id,
                                                    self.manufacturer)

    @staticmethod
    def insert_components():
        df = pd.read_csv('data/domesticdevices', names=['system_id', 'eiiscomponenttype_id', 'manufacturer_id', 'inpo_device_id', 'facility_id'], dtype={'facility_id': str})
        df.index = pd.np.arange(1, len(df) + 1)
        systems = {sys.eiis_code: sys.id for sys in System.query.all()}
        manufacturers = {man.name: man.id for man in Manufacturer.query.all()}
        df['system_id'].fillna('NA', inplace=True)
        df['system_id'] = df['system_id'].map(systems).apply(int)
        eiiscomponenttypes = {ct.eiis_code: ct.id for ct in EIISComponentType.query.all()}
        df['eiiscomponenttype_id'] = df['eiiscomponenttype_id'].map(eiiscomponenttypes).apply(int)
        facilities = {fac.docket: fac.id for fac in Facility.query.all()}
        df['facility_id'] = df['facility_id'].map(facilities).apply(int)
        df['manufacturer_id'] = df['manufacturer_id'].fillna('Other not listed').apply(lambda s:
                                                                                 'Other not listed' if not s.strip()
                                                                                 else s.strip())
        df['manufacturer_id'] = df['manufacturer_id'].map(manufacturers).apply(int)
        df.to_sql(con=db.engine, index=False, name=Component.__tablename__, if_exists='append')


class Manufacturer(db.Model):
    __tablename__ = 'manufacturers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    components = db.relationship('Component', backref='manufacturer', lazy='dynamic')

    def __repr__(self):
        return '<Manufacturer(%r, %r)>' % (self.id, self.name)

    @staticmethod
    def insert_manufacturers():
        df = pd.read_csv('data/domesticdevices', names=['system_id', 'eiiscomponenttype_id', 'manufacturer',
                                                   'inpo_device_id', 'facility_id'])
        df['manufacturer'] = df['manufacturer'].fillna('Other not listed')
        names = df['manufacturer'].drop_duplicates().apply(lambda s: 'Other not listed' if not s.strip() else s.strip())
        names.name = 'name'
        names.to_sql(con=db.engine, index=False, name=Manufacturer.__tablename__, if_exists='append')


class ComponentCause(db.Model):
    __tablename__ = 'componentcauses'
    id = db.Column(db.Integer, primary_key=True)
    cause_code = db.Column(db.String(1))
    cause_name = db.Column(db.String(64))
    description = db.Column(db.String(500))
    components = db.relationship('ComponentFailure', backref='componentcause', lazy='dynamic')

    def __repr__(self):
        return '<ComponentCause %r>' % self.cause_name

    @staticmethod
    def insert_componentcauses():
        with open('data/componentcauses') as file:
            reader = csv.reader(file)
            for row in reader:
                code, causename, description = row
                cmpcause = ComponentCause.query.filter_by(cause_code=code).first()
                if cmpcause is None:
                    cmpcause = ComponentCause(cause_code=code, cause_name=causename, description=description)
                    db.session.add(cmpcause)
            db.session.commit()


class ComponentFailure(db.Model):
    __tablename__ = 'componentfailures'
    ler_id = db.Column(db.Integer, db.ForeignKey('lers.id'), primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), primary_key=True)
    cause_id = db.Column(db.Integer, db.ForeignKey('componentcauses.id'))
    reportable_ices = db.Column(db.Boolean)

    def __repr__(self):
        return '<ComponentFailure(Component=%r, LER=%r)>' % (self.component_id, self.ler_id)


class LER(db.Model):
    __tablename__ = 'lers'
    id = db.Column(db.Integer, primary_key=True)
    facilities = db.relationship('Facility', secondary=facilitiesinvolved,
                                 backref=db.backref('lers', lazy='dynamic'),
                                 lazy='dynamic')
    title = db.Column(db.Text)
    event_date = db.Column(db.DateTime)
    ler_number = db.Column(db.String(64))
    report_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    operating_mode = db.Column(db.String(3))
    power_level = db.Column(db.Integer)
    cfrs = db.relationship('CFR', secondary=cfrselected, backref=db.backref('lers', lazy='dynamic'),
                           lazy='dynamic')
    abstract = db.Column(db.Text)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    components = db.relationship("ComponentFailure", backref="ler", lazy='dynamic')
    supplement_expected = db.Column(db.Boolean, default=False)
    supplement_date = db.Column(db.DateTime)
    approved = db.Column(db.Boolean, default=False)
    # approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))


    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronymn', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong',
                        'ul', 'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
                                                       tags=allowed_tags, strip=True))


    @staticmethod
    def generate_fake(count=5):
        from random import seed, randint, sample, choice
        import forgery_py

        seed()
        user_count = User.query.count()
        # facility_count = Facility.query.count()
        valid_facilities = [fac for fac in Facility.query.all() if fac.docket.startswith('0')]
        cfr_count = CFR.query.count()
        for i in range(count):
            seq = 1
            u = User.query.offset(randint(0, user_count - 1)).first()
            facilities = choice(valid_facilities)
            components = Component.query.filter_by(facility=facilities).all()
            try:
                components = sample(components, randint(0, 3))
            except ValueError:
                components = []

            event_date = forgery_py.date.date(True)
            ler_number = (facilities.docket[5:] if facilities.docket.startswith('0') \
                          else facilities.docket) + str(event_date.year) + '00{}R00'.format(seq)
            ler = LER.query.filter_by(ler_number=ler_number).first()
            if ler is not None:
                while ler is not None:
                    seq += 1
                    ler_number = (facilities.docket[5:] if facilities.docket.startswith('0') \
                                  else facilities.docket) + str(event_date.year) + '00{}R00'.format(seq)
                    ler = LER.query.filter_by(ler_number=ler_number).first()
            title = forgery_py.lorem_ipsum.sentence()
            operating_mode = ['N/A', '1', '2', '3', '4', '5'][randint(0, 5)]
            power_level = randint(0, 100)
            try:
                cfrs = sample(CFR.query.offset(randint(0, cfr_count - 1)).all(), randint(1, 4))
            except ValueError:
                cfrs = [CFR.query.all()[randint(1, 10)]]
            supplement_expected = choice([True, False])
            supplement_date = None
            if supplement_expected:
                supplement_date = forgery_py.date.date(True)
            abstract = forgery_py.lorem_ipsum.sentences(randint(10, 20))
            body = forgery_py.lorem_ipsum.sentences(randint(20, 50))
            ler = LER(author=u,
                      ler_number=ler_number,
                      facilities=[facilities],
                      title=title,
                      event_date=event_date,
                      operating_mode=operating_mode,
                      power_level=power_level,
                      cfrs=cfrs,
                      supplement_expected=supplement_expected,
                      supplement_date=supplement_date,
                      approved=choice([True, False]),
                      abstract=abstract,
                      body=body)
            components = [ComponentFailure(ler=ler,
                                           component=component,
                                           componentcause=choice(ComponentCause.query.all()),
                                           reportable_ices=choice([True, False])) for component in components]
            for component in components:
                ler.components.append(component)
            db.session.add(ler)
            db.session.commit()

    def __repr__(self):
        return '<LER %r>' % self.ler_number


db.event.listen(LER.body, 'set', LER.on_changed_body)


class Approve(db.Model):
    __tablename__ = 'approves'
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    ler_id = db.Column(db.Integer, db.ForeignKey('lers.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)