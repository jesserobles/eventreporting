#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role, CFR, Facility, Permission, EIISComponentType, System, ComponentCause, LER, \
    ComponentFailure, Component, Manufacturer
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_moment import Moment

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)
moment = Moment(app)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, CFR=CFR, Facility=Facility, Permission=Permission,
                EIISComponentType=EIISComponentType, System=System, ComponentCause=ComponentCause, LER=LER,
                Component=Component, ComponentFailure=ComponentFailure, Manufacturer=Manufacturer)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    """Run deployment tasks"""
    from flask_migrate import upgrade
    from app.models import Role,  Facility, Component, EIISComponentType, CFR, Manufacturer, System

    upgrade()

    # insert db data
    Role.insert_roles()
    CFR.insert_cfrs()
    Facility.insert_facilities()
    System.insert_systems()
    EIISComponentType.insert_eiiscomponenttypes()
    ComponentCause.insert_componentcauses()
    Manufacturer.insert_manufacturers()
    #Component.insert_components()


if __name__ == '__main__':
    manager.run()
